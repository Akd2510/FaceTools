# 🧪 FaceSwap Backend CURL Tests

This document provides example `curl` commands to test all endpoints exposed by the FaceSwap inference engine.

### 1. Health Check
Verify if the models are loaded and the service is healthy.
```bash
curl -X GET http://localhost:8000/swap/health
```

### 2. Swap via Multi-part Form Upload
Upload two local images to perform a face swap.
- `source_image`: The face you want to use.
- `target_image`: The image you want to swap the face into.
- `enhance`: (Optional) Boolean to enable GFPGAN restoration.

```bash
curl -X POST http://localhost:8000/swap \
  -F "source_image=@/path/to/source.jpg" \
  -F "target_image=@/path/to/target.jpg" \
  -F "enhance=true"
```

### 3. Swap via Remote URLs
Perform a swap using publicly accessible image URLs.
```bash
curl -X POST "http://localhost:8000/swap/url?source_url=https://example.com/source.jpg&target_url=https://example.com/target.jpg&enhance=true"
```

### 4. List Templates
Get a list of available template filenames.
```bash
curl -X GET http://localhost:8000/templates
```

### 5. Get Template Image
Download a specific template image by filename.
```bash
curl -X GET http://localhost:8000/templates/template1.jpg --output template1.jpg
```

---

**Note:** If running via the Nginx gateway, replace `localhost:8000` with `localhost/swap` or `localhost/templates` accordingly.
