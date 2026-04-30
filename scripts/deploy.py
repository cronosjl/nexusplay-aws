import boto3, json, os, zipfile, time

REGION  = "us-east-1"
PROJECT = "nexusplay"

SERVICES = {
    "game-service":         "services/game_service/lambda_function.py",
    "user-service":         "services/user_service/lambda_function.py",
    "notification-service": "services/notification_service/lambda_function.py",
}
STAGES = ["dev", "test", "prod"]

lambda_client = boto3.client("lambda",         region_name=REGION)
apigw_client  = boto3.client("apigateway",     region_name=REGION)
sns_client    = boto3.client("sns",            region_name=REGION)
sm_client     = boto3.client("secretsmanager", region_name=REGION)
iam_client    = boto3.client("iam",            region_name=REGION)


def get_account_id():
    return boto3.client("sts").get_caller_identity()["Account"]


def get_or_create_role():
    for role_name in ["NexusPlayLambdaRole", "LabRole"]:
        try:
            arn = iam_client.get_role(RoleName=role_name)["Role"]["Arn"]
            print(f"  ✅ Role found: {role_name}")
            return arn
        except iam_client.exceptions.NoSuchEntityException:
            continue
    role = iam_client.create_role(
        RoleName="NexusPlayLambdaRole",
        AssumeRolePolicyDocument=json.dumps({
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole"}]
        })
    )
    for p in [
        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
        "arn:aws:iam::aws:policy/AmazonSNSFullAccess",
        "arn:aws:iam::aws:policy/SecretsManagerReadWrite",
    ]:
        iam_client.attach_role_policy(RoleName="NexusPlayLambdaRole", PolicyArn=p)
    time.sleep(10)
    return role["Role"]["Arn"]


def zip_service(py_file, zip_path):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(py_file, "lambda_function.py")
    print(f"  ✅ Zipped: {zip_path}")


def deploy_lambda(name, py_file, role_arn, env_vars={}):
    full_name = f"{PROJECT}-{name}"
    zip_path  = f"/tmp/{name}.zip"
    zip_service(py_file, zip_path)
    with open(zip_path, "rb") as f:
        code = f.read()
    try:
        lambda_client.create_function(
            FunctionName=full_name, Runtime="python3.10",
            Role=role_arn, Handler="lambda_function.lambda_handler",
            Code={"ZipFile": code}, Timeout=30, MemorySize=128,
            Description=f"{name} - NexusPlay",
            Environment={"Variables": env_vars},
        )
        print(f"  🆕 Created: {full_name}")
        time.sleep(8)
    except lambda_client.exceptions.ResourceConflictException:
        lambda_client.update_function_code(FunctionName=full_name, ZipFile=code)
        if env_vars:
            lambda_client.update_function_configuration(
                FunctionName=full_name, Environment={"Variables": env_vars})
        print(f"  🔄 Updated: {full_name}")
        time.sleep(3)
    return lambda_client.get_function_configuration(FunctionName=full_name)["FunctionArn"]


def setup_sns():
    print("\n📢 Setting up SNS topic...")
    try:
        topic_arn = sns_client.create_topic(Name=f"{PROJECT}-alerts")["TopicArn"]
        print(f"  ✅ SNS Topic: {topic_arn}")
        return topic_arn
    except Exception as e:
        print(f"  ⚠️  SNS skipped: {e}")
        return ""


def setup_secrets(topic_arn):
    print("\n🔐 Setting up Secrets Manager...")
    secret_value = json.dumps({
        "db_password":   "nexusplay_secret_2024",
        "api_key":       "nxp_api_key_prod_xyz",
        "jwt_secret":    "nexusplay_jwt_secret",
        "sns_topic_arn": topic_arn,
    })
    try:
        sm_client.create_secret(
            Name=f"{PROJECT}/config",
            Description="NexusPlay configuration secrets",
            SecretString=secret_value,
        )
        print(f"  ✅ Secret created: {PROJECT}/config")
    except sm_client.exceptions.ResourceExistsException:
        sm_client.update_secret(SecretId=f"{PROJECT}/config", SecretString=secret_value)
        print(f"  🔄 Secret updated: {PROJECT}/config")


def setup_cloudwatch(lambda_arns):
    print("\n📊 Setting up CloudWatch alarms...")
    cw = boto3.client("cloudwatch", region_name=REGION)
    for name in lambda_arns:
        fn_name = f"{PROJECT}-{name}"
        for alarm_name, metric, threshold in [
            (f"{fn_name}-errors",   "Errors",   5),
            (f"{fn_name}-duration", "Duration", 5000),
        ]:
            try:
                cw.put_metric_alarm(
                    AlarmName=alarm_name, MetricName=metric,
                    Namespace="AWS/Lambda",
                    Dimensions=[{"Name": "FunctionName", "Value": fn_name}],
                    Period=60, EvaluationPeriods=1,
                    Threshold=threshold,
                    ComparisonOperator="GreaterThanThreshold",
                    Statistic="Sum" if metric == "Errors" else "Average",
                    TreatMissingData="notBreaching",
                )
            except Exception as e:
                print(f"  ⚠️  Alarm skipped {alarm_name}: {e}")
        print(f"  ✅ Alarms set: {fn_name}")


def create_api(lambda_arns):
    api_name = f"{PROJECT}-api"
    apis     = apigw_client.get_rest_apis().get("items", [])
    existing = next((a for a in apis if a["name"] == api_name), None)
    if existing:
        api_id = existing["id"]
        print(f"  ♻️  Existing API: {api_id}")
    else:
        api_id = apigw_client.create_rest_api(
            name=api_name,
            description="NexusPlay Microservices API",
            endpointConfiguration={"types": ["REGIONAL"]},
        )["id"]
        print(f"  🆕 Created API: {api_id}")
    root_id = apigw_client.get_resources(restApiId=api_id)["items"][0]["id"]
    routes  = {
        "games":         lambda_arns["game-service"],
        "users":         lambda_arns["user-service"],
        "notifications": lambda_arns["notification-service"],
    }
    for path, fn_arn in routes.items():
        _setup_resource(api_id, root_id, path, fn_arn)
    return api_id


def _setup_resource(api_id, root_id, path, fn_arn):
    resources   = apigw_client.get_resources(restApiId=api_id)["items"]
    existing    = next((r for r in resources if r.get("pathPart") == path), None)
    resource_id = existing["id"] if existing else apigw_client.create_resource(
        restApiId=api_id, parentId=root_id, pathPart=path)["id"]
    print(f"  ✅ Resource /{path} ready")
    account_id = get_account_id()
    uri = (f"arn:aws:apigateway:{REGION}:lambda:path"
           f"/2015-03-31/functions/{fn_arn}/invocations")
    for method in ["GET", "POST", "PUT", "DELETE"]:
        try:
            apigw_client.get_method(
                restApiId=api_id, resourceId=resource_id, httpMethod=method)
        except apigw_client.exceptions.NotFoundException:
            apigw_client.put_method(restApiId=api_id, resourceId=resource_id,
                httpMethod=method, authorizationType="NONE")
            apigw_client.put_integration(restApiId=api_id, resourceId=resource_id,
                httpMethod=method, type="AWS_PROXY",
                integrationHttpMethod="POST", uri=uri)
            print(f"     ✅ {method} /{path}")
    fn_name = fn_arn.split(":")[-1]
    try:
        lambda_client.add_permission(
            FunctionName=fn_name,
            StatementId=f"apigw-{path}-{api_id}",
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
            SourceArn=f"arn:aws:execute-api:{REGION}:{account_id}:{api_id}/*/*/{path}",
        )
    except lambda_client.exceptions.ResourceConflictException:
        pass


def deploy_stages(api_id):
    endpoints = {}
    for stage in STAGES:
        try:
            apigw_client.get_stage(restApiId=api_id, stageName=stage)
            print(f"  ♻️  Stage '{stage}' exists")
        except apigw_client.exceptions.NotFoundException:
            apigw_client.create_deployment(restApiId=api_id, stageName=stage)
            print(f"  🆕 Stage '{stage}' deployed")
        if stage == "prod":
            try:
                apigw_client.update_stage(restApiId=api_id, stageName=stage,
                    patchOperations=[
                        {"op": "replace", "path": "/cacheClusterEnabled", "value": "true"},
                        {"op": "replace", "path": "/cacheClusterSize",    "value": "0.5"},
                    ])
                print(f"  ✅ Cache enabled on prod")
            except Exception as e:
                print(f"  ⚠️  Cache skipped: {e}")
        endpoints[stage] = (f"https://{api_id}.execute-api"
                            f".{REGION}.amazonaws.com/{stage}")
    return endpoints


def save_config(api_id, lambda_arns, endpoints, topic_arn):
    config = {
        "api_id":      api_id,
        "region":      REGION,
        "lambda_arns": lambda_arns,
        "endpoints":   endpoints,
        "sns_topic":   topic_arn,
    }
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)
    print(f"\n  💾 Config saved → config.json")


def main():
    print("\n🚀 NexusPlay Deployment Starting...\n")

    print("🔑 Setting up IAM Role...")
    role_arn = get_or_create_role()
    print(f"   Role: {role_arn}")

    topic_arn = setup_sns()
    setup_secrets(topic_arn)

    print("\n📦 Deploying Lambda services...")
    base        = os.getcwd()
    lambda_arns = {}
    for name, rel_path in SERVICES.items():
        py_file = os.path.join(base, rel_path)
        env     = {"SNS_TOPIC_ARN": topic_arn} if name == "notification-service" else {}
        lambda_arns[name] = deploy_lambda(name, py_file, role_arn, env)

    setup_cloudwatch(lambda_arns)

    print("\n🌐 Creating API Gateway...")
    api_id = create_api(lambda_arns)

    print("\n📡 Deploying stages...")
    endpoints = deploy_stages(api_id)
    save_config(api_id, lambda_arns, endpoints, topic_arn)

    print("\n✅ NexusPlay deployed!\n" + "=" * 60)
    for stage, url in endpoints.items():
        print(f"  {stage.upper():5} → {url}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
