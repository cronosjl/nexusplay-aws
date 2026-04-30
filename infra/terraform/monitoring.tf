resource "aws_cloudwatch_dashboard" "nexusplay" {
  dashboard_name = "${var.project}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "Lambda Invocations"
          region  = var.region
          period  = 60
          stat    = "Sum"
          view    = "timeSeries"
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", "${var.project}-game-service"],
            ["AWS/Lambda", "Invocations", "FunctionName", "${var.project}-user-service"],
            ["AWS/Lambda", "Invocations", "FunctionName", "${var.project}-notification-service"]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "Lambda Errors"
          region  = var.region
          period  = 60
          stat    = "Sum"
          view    = "timeSeries"
          metrics = [
            ["AWS/Lambda", "Errors", "FunctionName", "${var.project}-game-service"],
            ["AWS/Lambda", "Errors", "FunctionName", "${var.project}-user-service"],
            ["AWS/Lambda", "Errors", "FunctionName", "${var.project}-notification-service"]
          ]
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title   = "Lambda Duration (ms)"
          region  = var.region
          period  = 60
          stat    = "Average"
          view    = "timeSeries"
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", "${var.project}-game-service"],
            ["AWS/Lambda", "Duration", "FunctionName", "${var.project}-user-service"],
            ["AWS/Lambda", "Duration", "FunctionName", "${var.project}-notification-service"]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title   = "ALB Request Count"
          region  = var.region
          period  = 60
          stat    = "Sum"
          view    = "timeSeries"
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", aws_lb.nexusplay_alb.arn_suffix]
          ]
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6
        properties = {
          title   = "ALB Response Time"
          region  = var.region
          period  = 60
          stat    = "Average"
          view    = "timeSeries"
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", aws_lb.nexusplay_alb.arn_suffix]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 12
        width  = 12
        height = 6
        properties = {
          title   = "Lambda Concurrent Executions"
          region  = var.region
          period  = 60
          stat    = "Maximum"
          view    = "timeSeries"
          metrics = [
            ["AWS/Lambda", "ConcurrentExecutions", "FunctionName", "${var.project}-game-service"],
            ["AWS/Lambda", "ConcurrentExecutions", "FunctionName", "${var.project}-user-service"]
          ]
        }
      }
    ]
  })
}

data "aws_sns_topic" "alerts" {
  name = "${var.project}-alerts"
}

resource "aws_cloudwatch_metric_alarm" "alb_5xx" {
  alarm_name          = "${var.project}-alb-5xx-errors"
  alarm_description   = "ALB 5XX errors too high"
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  evaluation_periods  = 2
  threshold           = 10
  comparison_operator = "GreaterThanThreshold"
  statistic           = "Sum"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [data.aws_sns_topic.alerts.arn]

  dimensions = {
    LoadBalancer = aws_lb.nexusplay_alb.arn_suffix
  }
}

resource "aws_cloudwatch_metric_alarm" "alb_latency" {
  alarm_name          = "${var.project}-alb-high-latency"
  alarm_description   = "ALB response time too high"
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  evaluation_periods  = 2
  threshold           = 2
  comparison_operator = "GreaterThanThreshold"
  statistic           = "Average"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [data.aws_sns_topic.alerts.arn]

  dimensions = {
    LoadBalancer = aws_lb.nexusplay_alb.arn_suffix
  }
}
