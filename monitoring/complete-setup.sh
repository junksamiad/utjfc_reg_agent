#!/bin/bash

# Complete the remaining backend configuration after health check update finishes
AWS_PROFILE="footballclub"
ENVIRONMENT_NAME="utjfc-backend-prod-3"

echo "⏳ Waiting for health check update to complete..."

# Wait for environment to be ready
while true; do
    STATUS=$(aws elasticbeanstalk describe-environments \
        --environment-names $ENVIRONMENT_NAME \
        --profile $AWS_PROFILE \
        --query 'Environments[0].Status' \
        --output text)
    
    echo "Current status: $STATUS"
    
    if [ "$STATUS" = "Ready" ]; then
        echo "✅ Environment is ready!"
        break
    elif [ "$STATUS" = "Terminated" ] || [ "$STATUS" = "Terminating" ]; then
        echo "❌ Environment terminated or terminating!"
        exit 1
    else
        echo "⏳ Still updating... waiting 30 seconds"
        sleep 30
    fi
done

echo ""
echo "🔧 Applying remaining configuration changes..."

# 1. Increase minimum instances to 2
echo "📈 Setting minimum instances to 2..."
aws elasticbeanstalk update-environment \
    --environment-name $ENVIRONMENT_NAME \
    --option-settings Namespace=aws:autoscaling:asg,OptionName=MinSize,Value=2 \
    --profile $AWS_PROFILE

# Wait for first update
echo "⏳ Waiting for scaling update..."
while true; do
    STATUS=$(aws elasticbeanstalk describe-environments \
        --environment-names $ENVIRONMENT_NAME \
        --profile $AWS_PROFILE \
        --query 'Environments[0].Status' \
        --output text)
    
    if [ "$STATUS" = "Ready" ]; then
        break
    else
        echo "⏳ Still updating scaling... waiting 30 seconds"
        sleep 30
    fi
done

# 2. Change auto-scaling to CPU-based
echo "🎯 Setting CPU-based auto-scaling..."
aws elasticbeanstalk update-environment \
    --environment-name $ENVIRONMENT_NAME \
    --option-settings \
        Namespace=aws:autoscaling:trigger,OptionName=MeasureName,Value=CPUUtilization \
        Namespace=aws:autoscaling:trigger,OptionName=UpperThreshold,Value=70 \
        Namespace=aws:autoscaling:trigger,OptionName=LowerThreshold,Value=20 \
    --profile $AWS_PROFILE

echo ""
echo "✅ All configuration updates applied!"
echo ""
echo "📊 Final Configuration:"
echo "- Health Check: HTTP:80/health (application-level)"
echo "- Min Instances: 2 (redundancy)"
echo "- Max Instances: 4 (cost-controlled scaling)"
echo "- Auto-scaling: CPU-based (70% up, 20% down)"
echo "- Instance Type: t3.small (2GB RAM)"
echo ""
echo "💰 Cost Impact:"
echo "- Before: 1 x t3.small = ~£12/month"
echo "- Now: 2 x t3.small = ~£24/month base"
echo "- Scale to 4 instances only during high CPU load"
echo ""
echo "🎯 Next Recommended Upgrade:"
echo "aws elasticbeanstalk update-environment \\"
echo "  --environment-name $ENVIRONMENT_NAME \\"
echo "  --option-settings Namespace=aws:autoscaling:launchconfiguration,OptionName=InstanceType,Value=t3.medium \\"
echo "  --profile $AWS_PROFILE"
echo ""
echo "💡 t3.medium (4GB RAM) recommended for AI photo processing workload"