output "alb_dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.nexusplay_alb.dns_name
}

output "alb_arn" {
  description = "ALB ARN"
  value       = aws_lb.nexusplay_alb.arn
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.nexusplay_vpc.id
}

output "dashboard_url" {
  description = "CloudWatch Dashboard URL"
  value       = "https://${var.region}.console.aws.amazon.com/cloudwatch/home?region=${var.region}#dashboards:name=${var.project}-dashboard"
}

output "route53_zone_id" {
  description = "Route53 Zone ID"
  value       = aws_route53_zone.nexusplay.zone_id
}
