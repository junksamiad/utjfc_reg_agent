#!/bin/bash

# AWS Cost Management Setup Script
AWS_PROFILE="footballclub"
EMAIL="your-email@domain.com"  # Replace with your email

echo "💰 Setting up AWS cost management..."

# 1. Create SNS topic for cost alerts
echo "📧 Creating cost alerts SNS topic..."
COST_TOPIC_ARN=$(aws sns create-topic \
    --name "utjfc-cost-alerts" \
    --profile $AWS_PROFILE \
    --output text --query 'TopicArn')

echo "📧 Cost alerts topic created: $COST_TOPIC_ARN"

# 2. Subscribe email to cost alerts
echo "📧 Subscribe to cost alerts:"
echo "aws sns subscribe --topic-arn $COST_TOPIC_ARN --protocol email --notification-endpoint $EMAIL --profile $AWS_PROFILE"

# 3. Create monthly budget with alerts
echo "💸 Creating monthly budget..."

# Create budget JSON
cat > /tmp/budget.json << EOF
{
  "BudgetName": "UTJFC-Monthly-Budget",
  "BudgetLimit": {
    "Amount": "50.00",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST",
  "CostFilters": {},
  "TimePeriod": {
    "Start": "$(date -d 'first day of this month' '+%Y-%m-01')",
    "End": "2087-06-15"
  }
}
EOF

# Create budget alerts JSON
cat > /tmp/budget-notifications.json << EOF
[
  {
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 80.0,
      "ThresholdType": "PERCENTAGE"
    },
    "Subscribers": [
      {
        "SubscriptionType": "SNS",
        "Address": "$COST_TOPIC_ARN"
      }
    ]
  },
  {
    "Notification": {
      "NotificationType": "FORECASTED",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 100.0,
      "ThresholdType": "PERCENTAGE"
    },
    "Subscribers": [
      {
        "SubscriptionType": "SNS",
        "Address": "$COST_TOPIC_ARN"
      }
    ]
  }
]
EOF

# Create the budget
aws budgets create-budget \
    --account-id $(aws sts get-caller-identity --profile $AWS_PROFILE --query Account --output text) \
    --budget file:///tmp/budget.json \
    --notifications-with-subscribers file:///tmp/budget-notifications.json \
    --profile $AWS_PROFILE

echo "✅ Budget created successfully!"

# Cleanup temp files
rm /tmp/budget.json /tmp/budget-notifications.json

echo ""
echo "💰 Cost Management Setup Complete!"
echo ""
echo "📊 Budget Details:"
echo "- Monthly limit: $50 USD"
echo "- Alert at 80% actual spend ($40)"
echo "- Alert at 100% forecasted spend ($50)"
echo ""
echo "📧 To receive alerts, run:"
echo "aws sns subscribe --topic-arn $COST_TOPIC_ARN --protocol email --notification-endpoint YOUR_EMAIL@domain.com --profile $AWS_PROFILE"
echo ""
echo "🔧 View/modify budgets:"
echo "https://console.aws.amazon.com/billing/home#/budgets"
echo ""
echo "💡 AWS Billing Features:"
echo "1. 📊 Budgets: Alerts only (no automatic stopping)"
echo "2. 🔒 Organizations: Can set hard limits with Service Control Policies"
echo "3. 📈 Cost Explorer: Analyze spending patterns"
echo "4. 🏷️  Cost Allocation Tags: Track costs by resource"