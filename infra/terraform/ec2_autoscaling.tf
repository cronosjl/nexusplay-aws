# 1. LE SECURITY GROUP
resource "aws_security_group" "ec2_sg" {
  name        = "${var.project}-ec2-sg"
  description = "Security group for NexusPlay EC2 instances"
  vpc_id      = aws_vpc.nexusplay_vpc.id

  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project}-ec2-sg" }
}

# 2. LE TARGET GROUP
resource "aws_lb_target_group" "ec2_tg" {
  name     = "${var.project}-ec2-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.nexusplay_vpc.id

  health_check {
    path                = "/health"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
  lifecycle {
    ignore_changes = [tags, tags_all]
  }
}

# 3. LE LAUNCH TEMPLATE (Nettoyé de l'IAM)
resource "aws_launch_template" "nexusplay" {
  name_prefix   = "${var.project}-lt-"
  image_id      = "ami-0c02fb55956c7d316"
  instance_type = "t2.micro"


  network_interfaces {
    associate_public_ip_address = true
    security_groups             = [aws_security_group.ec2_sg.id]
  }
  lifecycle {
    ignore_changes = [tags, tags_all]
  }
  user_data = base64encode(<<-USERDATA
    #!/bin/bash
    yum update -y
    yum install -y python3 python3-pip
    pip3 install flask

    cat > /home/ec2-user/app.py << 'PYEOF'
    from flask import Flask, jsonify
    import math

    app = Flask(__name__)

    @app.route('/health')
    def health():
        return jsonify({"status": "healthy"})

    @app.route('/stress')
    def stress():
        res = 0
        for i in range(10**7):
            res += math.sqrt(i)
        return jsonify({"status": "stressing"})

    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=80)
    PYEOF

    python3 /home/ec2-user/app.py &
  USERDATA
  )
}

# 4. L'AUTO SCALING GROUP
resource "aws_autoscaling_group" "nexusplay" {
  name                = "${var.project}-asg"
  min_size            = 1
  max_size            = 5
  desired_capacity    = 2
  vpc_zone_identifier = [aws_subnet.public_a.id, aws_subnet.public_b.id]
  target_group_arns   = [aws_lb_target_group.ec2_tg.arn]

  launch_template {
    id      = aws_launch_template.nexusplay.id
    version = "$Latest"
  }
}

# 5. L'ALARME DE SCALING (Plus sensible pour compenser)
resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "${var.project}-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"            # On réagit plus vite
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "60"           # 1 minute
  statistic           = "Average"
  threshold           = "0.1"
  alarm_actions       = [aws_autoscaling_policy.scale_up.arn]

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.nexusplay.name
  }
}

# 6. LA POLITIQUE DE SCALING UP
resource "aws_autoscaling_policy" "scale_up" {
  name                   = "${var.project}-scale-up"
  scaling_adjustment     = 2
  adjustment_type        = "ChangeInCapacity"
  cooldown                = 60
  autoscaling_group_name = aws_autoscaling_group.nexusplay.name
}
