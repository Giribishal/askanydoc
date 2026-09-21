# Account-level billing control for AskAnyDoc's Amazon Bedrock usage.
# AWS Budgets notifications are delayed billing alerts, not real-time hard stops.
# The live budget was first created in the AWS console on 2026-09-20. Before
# enabling this resource with notification emails, import that live budget:
# terraform import 'aws_budgets_budget.askanydoc_bedrock_monthly[0]' '404584456165:askanydoc-bedrock-monthly'

variable "budget_notification_emails" {
  description = "Email addresses that receive AskAnyDoc Bedrock budget alerts. Keep real addresses in an ignored .tfvars file."
  type        = set(string)
  default     = []
}

resource "aws_budgets_budget" "askanydoc_bedrock_monthly" {
  count = length(var.budget_notification_emails) > 0 ? 1 : 0

  name         = "askanydoc-bedrock-monthly"
  budget_type  = "COST"
  limit_amount = "25"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  cost_filter {
    name = "Service"
    values = [
      "Amazon Bedrock",
      "Claude Haiku 4.5 (Amazon Bedrock Edition)",
    ]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 10
    threshold_type             = "ABSOLUTE_VALUE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = tolist(var.budget_notification_emails)
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 15
    threshold_type             = "ABSOLUTE_VALUE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = tolist(var.budget_notification_emails)
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 20
    threshold_type             = "ABSOLUTE_VALUE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = tolist(var.budget_notification_emails)
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 25
    threshold_type             = "ABSOLUTE_VALUE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = tolist(var.budget_notification_emails)
  }
}
