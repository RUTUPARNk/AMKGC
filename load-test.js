import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 100,
  duration: '30s',
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests should be below 500ms
    http_req_failed: ['rate<0.01'],   // Error rate should be less than 1%
  },
};

export default function () {
  // Test health endpoint
  const healthRes = http.get('http://localhost:8000/api/health');
  check(healthRes, {
    'health status is 200': (r) => r.status === 200,
  });
  
  // Test pipeline execution endpoint
  const pipelineRes = http.post('http://localhost:8000/api/v1/run_pipeline',
    JSON.stringify({
      pipeline: 'summarize_and_translate',
      input_data: {
        text: 'This is a test text for load testing the Node-LLM System pipeline execution.'
      }
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  check(pipelineRes, {
    'pipeline execution status is 200': (r) => r.status === 200,
  });
  
  sleep(1);
}
