#!/bin/bash

# ==============================================================================
# SCRIPT CẬP NHẬT & TRIỂN KHAI DMX PRICE TRACKER QUA GOOGLE CLOUD CONSOLE CLI
# ==============================================================================

PROJECT_ID="graphic-mission-503107-h2"
REGION="asia-east1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/dmx-price-tracker:latest"
JOB_NAME="dmx-price-tracker-job"

echo "========================================================================="
echo "🚀 ĐANG CẬP NHẬT DMX PRICE TRACKER LÊN GOOGLE CLOUD VIA GCLOUD CLI..."
echo "========================================================================="

# 1. Check gcloud CLI
if ! command -v gcloud &> /dev/null
then
    echo "❌ Lỗi: gcloud CLI chưa được cài đặt hoặc chưa có trong PATH."
    exit 1
fi

# 2. Config GCP Project
gcloud config set project $PROJECT_ID

# 3. Build & Push Image
echo "📦 1/3. Đang build container image mới nhất trên Cloud Build..."
gcloud builds submit --tag $IMAGE_NAME .

if [ $? -ne 0 ]; then
    echo "❌ Build thất bại!"
    exit 1
fi

# 4. Create or Update Cloud Run Job
echo "⚡ 2/3. Đang cập nhật Cloud Run Job..."
gcloud run jobs describe $JOB_NAME --region=$REGION &> /dev/null
if [ $? -eq 0 ]; then
    gcloud run jobs update $JOB_NAME \
        --image $IMAGE_NAME \
        --region $REGION
else
    gcloud run jobs create $JOB_NAME \
        --image $IMAGE_NAME \
        --region $REGION \
        --max-retries 1
fi

# 5. Trigger Test Run
echo "🔥 3/3. Đang kích hoạt chạy thử nghiệm ngay lập tức..."
gcloud run jobs execute $JOB_NAME --region $REGION --wait

echo "========================================================================="
echo "✅ HOÀN THÀNH CẬP NHẬT VÀ CHẠY THỬ TRÊN GOOGLE CLOUD CONSOLE CLI!"
echo "========================================================================="
