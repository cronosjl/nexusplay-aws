# ─── APPLICATION LOAD BALANCER ───────────────────────────────────
resource "aws_lb" "nexusplay_alb" {
  name               = "${var.project}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = [aws_subnet.public_a.id, aws_subnet.public_b.id]

  enable_deletion_protection = false

  tags = {
    Name        = "${var.project}-alb"
    Environment = var.environment
    Project     = var.project
  }
}

# ─── TARGET GROUPS ───────────────────────────────────────────────
resource "aws_lb_target_group" "games_tg" {
  name        = "${var.project}-games-tg"
  target_type = "lambda"

  tags = {
    Name    = "${var.project}-games-tg"
    Project = var.project
  }
}

resource "aws_lb_target_group" "users_tg" {
  name        = "${var.project}-users-tg"
  target_type = "lambda"

  tags = {
    Name    = "${var.project}-users-tg"
    Project = var.project
  }
}

resource "aws_lb_target_group" "notifications_tg" {
  name        = "${var.project}-notif-tg"
  target_type = "lambda"

  tags = {
    Name    = "${var.project}-notif-tg"
    Project = var.project
  }
}

# ─── LISTENER HTTP ───────────────────────────────────────────────
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.nexusplay_alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.games_tg.arn
  }
}

# ─── LISTENER RULES (routing par path) ───────────────────────────
resource "aws_lb_listener_rule" "games_rule" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.games_tg.arn
  }

  condition {
    path_pattern {
      values = ["/games*"]
    }
  }
}

resource "aws_lb_listener_rule" "users_rule" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 200

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.users_tg.arn
  }

  condition {
    path_pattern {
      values = ["/users*"]
    }
  }
}

resource "aws_lb_listener_rule" "notifications_rule" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 300

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.notifications_tg.arn
  }

  condition {
    path_pattern {
      values = ["/notifications*"]
    }
  }
}

# ─── LAMBDA PERMISSIONS POUR ALB ─────────────────────────────────
data "aws_lambda_function" "game_service" {
  function_name = "${var.project}-game-service"
}

data "aws_lambda_function" "user_service" {
  function_name = "${var.project}-user-service"
}

data "aws_lambda_function" "notification_service" {
  function_name = "${var.project}-notification-service"
}

resource "aws_lambda_permission" "alb_game" {
  statement_id  = "AllowALBGameService"
  action        = "lambda:InvokeFunction"
  function_name = data.aws_lambda_function.game_service.function_name
  principal     = "elasticloadbalancing.amazonaws.com"
  source_arn    = aws_lb_target_group.games_tg.arn
}

resource "aws_lambda_permission" "alb_user" {
  statement_id  = "AllowALBUserService"
  action        = "lambda:InvokeFunction"
  function_name = data.aws_lambda_function.user_service.function_name
  principal     = "elasticloadbalancing.amazonaws.com"
  source_arn    = aws_lb_target_group.users_tg.arn
}

resource "aws_lambda_permission" "alb_notification" {
  statement_id  = "AllowALBNotificationService"
  action        = "lambda:InvokeFunction"
  function_name = data.aws_lambda_function.notification_service.function_name
  principal     = "elasticloadbalancing.amazonaws.com"
  source_arn    = aws_lb_target_group.notifications_tg.arn
}

# ─── ATTACH LAMBDAS TO TARGET GROUPS ─────────────────────────────
resource "aws_lb_target_group_attachment" "games_attach" {
  target_group_arn = aws_lb_target_group.games_tg.arn
  target_id        = data.aws_lambda_function.game_service.arn
  depends_on       = [aws_lambda_permission.alb_game]
}

resource "aws_lb_target_group_attachment" "users_attach" {
  target_group_arn = aws_lb_target_group.users_tg.arn
  target_id        = data.aws_lambda_function.user_service.arn
  depends_on       = [aws_lambda_permission.alb_user]
}

resource "aws_lb_target_group_attachment" "notifications_attach" {
  target_group_arn = aws_lb_target_group.notifications_tg.arn
  target_id        = data.aws_lambda_function.notification_service.arn
  depends_on       = [aws_lambda_permission.alb_notification]
}
