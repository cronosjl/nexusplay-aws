# ─── ROUTE 53 HOSTED ZONE ────────────────────────────────────────
resource "aws_route53_zone" "nexusplay" {
  name = "nexusplay.internal"

  tags = {
    Name    = "${var.project}-zone"
    Project = var.project
  }
}

# ─── RECORD PRIMARY (Active) ──────────────────────────────────────
resource "aws_route53_record" "api_primary" {
  zone_id = aws_route53_zone.nexusplay.zone_id
  name    = "api.nexusplay.internal"
  type    = "A"

  alias {
    name                   = aws_lb.nexusplay_alb.dns_name
    zone_id                = aws_lb.nexusplay_alb.zone_id
    evaluate_target_health = true
  }

  failover_routing_policy {
    type = "PRIMARY"
  }

  set_identifier  = "primary"
  health_check_id = aws_route53_health_check.primary.id
}

# ─── RECORD SECONDARY (Backup) ───────────────────────────────────
resource "aws_route53_record" "api_secondary" {
  zone_id = aws_route53_zone.nexusplay.zone_id
  name    = "api.nexusplay.internal"
  type    = "A"

  alias {
    name                   = aws_lb.nexusplay_alb.dns_name
    zone_id                = aws_lb.nexusplay_alb.zone_id
    evaluate_target_health = false
  }

  failover_routing_policy {
    type = "SECONDARY"
  }

  set_identifier = "secondary"
}

# ─── HEALTH CHECK ────────────────────────────────────────────────
resource "aws_route53_health_check" "primary" {
  fqdn              = aws_lb.nexusplay_alb.dns_name
  port              = 80
  type              = "HTTP"
  resource_path     = "/games"
  failure_threshold = 3
  request_interval  = 30

  tags = {
    Name    = "${var.project}-health-check"
    Project = var.project
  }
}
