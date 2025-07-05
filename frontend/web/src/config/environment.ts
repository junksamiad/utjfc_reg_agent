// Environment configuration for API endpoints
const isDevelopment = process.env.NODE_ENV === 'development';

export const config = {
  API_BASE_URL: isDevelopment 
    ? 'http://localhost:8000'
    : 'https://d1ahgtos8kkd8y.cloudfront.net/api',
  
  // Individual endpoint URLs
  get UPLOAD_URL() {
    return `${this.API_BASE_URL}/upload-async`;
  },
  
  get UPLOAD_STATUS_URL() {
    return `${this.API_BASE_URL}/upload-status`;
  },
  
  get CHAT_URL() {
    return `${this.API_BASE_URL}/chat`;
  }
};

export default config; 