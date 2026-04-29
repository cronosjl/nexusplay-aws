import os
import json
import zipfile
import time
import boto3

REGION = "us-east-1"
PROJECT = "nexusplay"

# Chemins vers tes services
SERVICES = {
    "game-service": "services/game_service/lambda_function.py",
    "user-service": "services/user_service/lambda_function.py",
    "notification-service": "services/notification_service/lambda_function.py",
}
STAGES = ["dev", "test", "prod"]

lambda_client = boto3.client("lambda", region_name=REGION)
apigw_client = boto3.client("apigateway", region_name=REGION)
sns_client = boto3.client("sns", region_name=REGION)
sm_client = boto3.client("secretsmanager", region_name=REGION)
iam_client = boto3.client("iam", region_name=REGION)


def get_account_id():
    return boto3.client("sts").get_caller_identity()["Account"]


def get_or_create_role():
    role_name = "NexusPlayLambdaRole"
    try:
        return iam_client.get_role(RoleName=role_name)["Role"]["Arn"]
    except iam_client.exceptions.NoSuchEntityException:
        print(f"  🆕 Création du rôle : {role_name}")
        role = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }]
            })
        )
        policies = [
            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
            "arn:aws:iam::aws:policy/AmazonSNSFullAccess",
            "arn:aws:iam::aws:policy/SecretsManagerReadWrite"
        ]
        for p in policies:
            iam_client.attach_role_policy(RoleName=role_name, PolicyArn=p)
        time.sleep(10)
        return role["Role"]["Arn"]


def zip_service(service_name, source_file):
    zip_path = f"/tmp/{service_name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(source_file, "lambda_function.py")
    return zip_path


def deploy_lambda(name, source_file, role_arn):
    full_name = f"{PROJECT}-{name}"
    zip_p = zip_service(name, source_file)
    with open(zip_p, "rb") as f:
        payload = f.read()

    try:
        lambda_client.create_function(
            FunctionName=full_name, Runtime="python3.10",
            Role=role_arn, Handler="lambda_function.lambda_handler",
            Code={"ZipFile": payload}, Timeout=15, MemorySize=128
        )
        print(f"  🆕 Lambda créée : {full_name}")
    except lambda_client.exceptions.ResourceConflictException:
        lambda_client.update_function_code(FunctionName=full_name, ZipFile=payload)
        print(f"  🔄 Lambda mise à jour : {full_name}")

    return lambda_client.get_function_configuration(FunctionName=full_name)["FunctionArn"]


def create_api_structure(lambda_arns):
    api_name = f"{PROJECT}-api"
    apis = apigw_client.get_rest_apis().get("items", [])
    api = next((a for a in apis if a["name"] == api_name), None)

    if not api:
        api = apigw_client.create_rest_api(
            name=api_name,
            endpointConfiguration={"types": ["REGIONAL"]}
        )
        api_id = api["id"]
    else:
        api_id = api["id"]

    root_id = apigw_client.get_resources(restApiId=api_id)["items"][0]["id"]

    for path, service_key in [("games", "game-service"), ("users", "user-service")]:
        resources = apigw_client.get_resources(restApiId=api_id)["items"]
        res = next((r for r in resources if r.get("pathPart") == path), None)
        if not res:
            res = apigw_client.create_resource(restApiId=api_id, parentId=root_id, pathPart=path)
        res_id = res["id"]

        uri = f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arns[service_key]}/invocations"

        try:
            apigw_client.put_method(restApiId=api_id, resourceId=res_id, httpMethod="GET", authorizationType="NONE")
            apigw_client.put_integration(
                restApiId=api_id, resourceId=res_id, httpMethod="GET",
                type="AWS_PROXY", integrationHttpMethod="POST", uri=uri
            )
        except Exception:
            pass

        try:
            lambda_client.add_permission(
                FunctionName=f"{PROJECT}-{service_key}",
                StatementId=f"apigw-access-{int(time.time())}",
                Action="lambda:InvokeFunction",
                Principal="apigateway.amazonaws.com"
            )
        except Exception:
            pass

    return api_id


def main():
    print("🚀 Déploiement complet...")
    role_arn = get_or_create_role()

    base_dir = os.getcwd()
    lambda_arns = {}
    for name, rel_path in SERVICES.items():
        abs_path = os.path.join(base_dir, rel_path)
        lambda_arns[name] = deploy_lambda(name, abs_path, role_arn)

    api_id = create_api_structure(lambda_arns)
    apigw_client.create_deployment(restApiId=api_id, stageName="prod")

    print(f"\n✅ Terminé ! URL : https://{api_id}.execute-api.{REGION}.amazonaws.com/prod/games")


if __name__ == "__main__":
    main()