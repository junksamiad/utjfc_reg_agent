#!/bin/bash

# UTJFC Backend Monitoring Setup Script
# Sets up CloudWatch alarms and improves instance configuration

AWS_PROFILE="footballclub"
ENVIRONMENT_NAME="utjfc-backend-prod-3"
APPLICATION_NAME="utjfc-registration-backend"

echo "🚨 Setting up monitoring for UTJFC Backend..."

# 1. Create SNS topic for alerts
echo "📧 Creating SNS topic for alerts..."
TOPIC_ARN=$(aws sns create-topic \
    --name "utjfc-backend-alerts" \
    --profile $AWS_PROFILE \
    --output text --query 'TopicArn')

echo "📧 SNS Topic created: $TOPIC_ARN"

# 2. Subscribe email to SNS topic (replace with your email)
echo "📧 Subscribe to alerts:"
echo "aws sns subscribe --topic-arn $TOPIC_ARN --protocol email --notification-endpoint your-email@domain.com --profile $AWS_PROFILE"

# 3. Create CloudWatch alarms
echo "⏰ Creating CloudWatch alarms..."

# High CPU Alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "UTJFC-Backend-HighCPU" \
    --alarm-description "Alert when backend CPU usage exceeds 80%" \
    --metric-name CPUUtilization \
    --namespace AWS/EC2 \
    --statistic Average \
    --period 300 \
    --evaluation-periods 2 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --alarm-actions "$TOPIC_ARN" \
    --dimensions Name=EnvironmentName,Value=$ENVIRONMENT_NAME \
    --profile $AWS_PROFILE

# Environment Health Alarm  
aws cloudwatch put-metric-alarm \
    --alarm-name "UTJFC-Backend-EnvironmentHealth" \
    --alarm-description "Alert when environment health is not Green" \
    --metric-name EnvironmentHealth \
    --namespace AWS/ElasticBeanstalk \
    --statistic Average \
    --period 60 \
    --evaluation-periods 2 \
    --threshold 15 \
    --comparison-operator LessThanThreshold \
    --alarm-actions "$TOPIC_ARN" \
    --dimensions Name=EnvironmentName,Value=$ENVIRONMENT_NAME \
    --profile $AWS_PROFILE

# 5xx Error Rate Alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "UTJFC-Backend-ApplicationErrors" \
    --alarm-description "Alert when 5xx error rate exceeds 5 per 5 minutes" \
    --metric-name ApplicationRequests5xx \
    --namespace AWS/ElasticBeanstalk \
    --statistic Sum \
    --period 300 \
    --evaluation-periods 1 \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold \
    --alarm-actions "$TOPIC_ARN" \
    --dimensions Name=EnvironmentName,Value=$ENVIRONMENT_NAME \
    --profile $AWS_PROFILE

echo "✅ CloudWatch alarms created successfully!"

# 4. Configuration recommendations
echo ""
echo "🔧 RECOMMENDED CONFIGURATION UPDATES:"
echo ""
echo "1. Upgrade Instance Type (current: t3.small with 2GB RAM):"
echo "   aws elasticbeanstalk update-environment \\"
echo "     --environment-name $ENVIRONMENT_NAME \\"
echo "     --option-settings Namespace=aws:autoscaling:launchconfiguration,OptionName=InstanceType,Value=t3.medium \\"
echo "     --profile $AWS_PROFILE"
echo ""
echo "2. Increase minimum instances for redundancy:"
echo "   aws elasticbeanstalk update-environment \\"
echo "     --environment-name $ENVIRONMENT_NAME \\"
echo "     --option-settings Namespace=aws:autoscaling:asg,OptionName=MinSize,Value=2 \\"
echo "     --profile $AWS_PROFILE"
echo ""
echo "3. Change auto-scaling trigger to CPU-based:"
echo "   aws elasticbeanstalk update-environment \\"
echo "     --environment-name $ENVIRONMENT_NAME \\"
echo "     --option-settings Namespace=aws:autoscaling:trigger,OptionName=MeasureName,Value=CPUUtilization \\"
echo "                      Namespace=aws:autoscaling:trigger,OptionName=UpperThreshold,Value=70 \\"
echo "                      Namespace=aws:autoscaling:trigger,OptionName=LowerThreshold,Value=20 \\"
echo "     --profile $AWS_PROFILE"
echo ""
echo "4. Add health check endpoint to your FastAPI app:"
echo "   @app.get('/health')"
echo "   def health_check():"
echo "       return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}"
echo ""
echo "5. Update ELB health check to use /health endpoint:"
echo "   aws elasticbeanstalk update-environment \\"
echo "     --environment-name $ENVIRONMENT_NAME \\"
echo "     --option-settings Namespace=aws:elb:healthcheck,OptionName=Target,Value=HTTP:80/health \\"
echo "     --profile $AWS_PROFILE"

echo ""
echo "🎯 IMMEDIATE RISK MITIGATION:"
echo "The current single t3.small instance (2GB RAM) is insufficient for AI photo processing."
echo "Recommend immediate upgrade to t3.medium (4GB RAM) and 2 minimum instances."
echo ""
echo "📊 Monitor dashboard: https://console.aws.amazon.com/cloudwatch/home?region=eu-north-1#alarmsV2:"
echo ""
echo "🚨 To set up email alerts, run:"
echo "aws sns subscribe --topic-arn $TOPIC_ARN --protocol email --notification-endpoint YOUR_EMAIL@domain.com --profile $AWS_PROFILE"