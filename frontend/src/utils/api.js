import axios from "axios";

const API_BASE = process.env.REACT_APP_API_URL || "";

const api = axios.create({
  baseURL: `${API_BASE}/api`,
  timeout: 120000,
});

// --- Images ---
export const uploadImages = (files, onProgress) => {
  const formData = new FormData();
  files.forEach((f) => formData.append("images", f));
  return api.post("/images/upload/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => {
      if (onProgress) onProgress(Math.round((e.loaded / e.total) * 100));
    },
  });
};

export const fetchImages = (page = 1) => api.get(`/images/?page=${page}`);

export const fetchImage = (id) => api.get(`/images/${id}/`);

export const deleteImage = (id) => api.delete(`/images/${id}/`);

// --- Clusters ---
export const fetchClusters = () => api.get("/clusters/");

export const fetchCluster = (id) => api.get(`/clusters/${id}/`);

export const labelCluster = (id, person_label) =>
  api.patch(`/clusters/${id}/`, { person_label });

export const triggerRecluster = () => api.post("/clusters/recluster/");

// --- Search ---
export const searchByFile = (file, top_k = 10) => {
  const formData = new FormData();
  formData.append("query_image", file);
  formData.append("top_k", top_k);
  return api.post("/search/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const searchByImageId = (image_id, top_k = 10) =>
  api.post("/search/", { image_id, top_k });

// --- Stats ---
export const fetchStats = () => api.get("/stats/");

export default api;
