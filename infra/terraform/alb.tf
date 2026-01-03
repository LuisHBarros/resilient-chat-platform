# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${local.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = var.environment == "prod" ? true : false
  enable_http2               = true
  enable_cross_zone_load_balancing = true

  tags = {
    Name = "${local.name_prefix}-alb"
  }
}

# Target Group
resource "aws_lb_target_group" "app" {
  name        = "${local.name_prefix}-tg"
  port        = var.app_port
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/health"
    protocol            = "HTTP"
    matcher            = "200"
  }

  # Deregistration delay for graceful shutdown
  deregistration_delay = 30

  tags = {
    Name = "${local.name_prefix}-tg"
  }
}

# HTTP Listener (redirects to HTTPS in production)
resource "aws_lb_listener" "app" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }

  # In production, you might want to redirect HTTP to HTTPS:
  # default_action {
  #   type = "redirect"
  #   redirect {
  #     port        = "443"
  #     protocol    = "HTTPS"
  #     status_code = "HTTP_301"
  #   }
  # }
}

# Optional: HTTPS Listener (requires ACM certificate)
# Uncomment and configure if you have a domain and SSL certificate
# resource "aws_lb_listener" "app_https" {
#   load_balancer_arn = aws_lb.main.arn
#   port              = "443"
#   protocol          = "HTTPS"
#   ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
#   certificate_arn   = aws_acm_certificate.app.arn
#
#   default_action {
#     type             = "forward"
#     target_group_arn = aws_lb_target_group.app.arn
#   }
# }

