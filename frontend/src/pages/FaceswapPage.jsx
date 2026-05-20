import React, { useState, useEffect, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import axios from "axios";
import {
  Card,
  Button,
  Badge,
  Spinner,
  SectionHeader,
  Thumb,
} from "../components/UI";

const API_BASE = process.env.REACT_APP_API_URL || "";

export default function FaceswapPage() {
  const [templates, setTemplates] = useState([]);
  const [sourceFile, setSourceFile] = useState(null);
  const [templateFile, setTemplateFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [resultImage, setResultImage] = useState(null);
  const [enhance, setEnhance] = useState(true);
  const [error, setError] = useState(null);
  const [warnings, setWarnings] = useState([]);

  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const res = await axios.get(API_BASE + "/templates");
        setTemplates(res.data.templates);
      } catch (err) {
        console.error("Failed to fetch templates:", err);
      }
    };
    fetchTemplates();
  }, []);

  const onDropSource = useCallback((accepted) => {
    if (accepted[0]) {
      setSourceFile(
        Object.assign(accepted[0], {
          preview: URL.createObjectURL(accepted[0]),
        }),
      );
      setResultImage(null);
    }
  }, []);

  const onDropCustomTemplate = useCallback((accepted) => {
    if (accepted[0]) {
      setTemplateFile(
        Object.assign(accepted[0], {
          preview: URL.createObjectURL(accepted[0]),
          filename: accepted[0].name,
        }),
      );
      setResultImage(null);
    }
  }, []);

  const {
    getRootProps: getSourceProps,
    getInputProps: getSourceInput,
    isDragActive: sourceActive,
  } = useDropzone({
    onDrop: onDropSource,
    accept: { "image/*": [] },
    multiple: false,
  });

  const { getRootProps: getCustomProps, getInputProps: getCustomInput } =
    useDropzone({
      onDrop: onDropCustomTemplate,
      accept: { "image/*": [] },
      multiple: false,
    });

  const selectGridTemplate = async (filename) => {
    try {
      const res = await axios.get(API_BASE + "/templates/" + filename, {
        responseType: "blob",
      });
      const file = new File([res.data], filename, { type: res.data.type });
      setTemplateFile(
        Object.assign(file, {
          preview: URL.createObjectURL(file),
          filename: filename,
        }),
      );
      setResultImage(null);
    } catch (err) {
      setError("Failed to load template image.");
    }
  };

  const handleSwap = async () => {
    if (!sourceFile || !templateFile || isProcessing) return;
    setIsProcessing(true);
    setError(null);
    setWarnings([]);
    setResultImage(null);
    const formData = new FormData();
    formData.append("source_image", sourceFile);
    formData.append("target_image", templateFile);
    formData.append("enhance", enhance);
    try {
      const res = await axios.post(API_BASE + "/swap", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      if (res.data.result) {
        setResultImage("data:image/png;base64," + res.data.result);
        if (res.data.warnings) setWarnings(res.data.warnings);
      } else {
        setError(res.data.error || "Swap failed.");
      }
    } catch (err) {
      setError(err.response?.data?.error || "Connection error.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto" }}>
      <SectionHeader
        title="FaceSwap Pro"
        subtitle="Swap identities across images using AI"
      />
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr",
          gap: "1.5rem",
          alignItems: "start",
        }}
      >
        <Card>
          <div
            style={{
              fontWeight: 700,
              marginBottom: "1rem",
              fontSize: "0.9rem",
              color: "var(--text-secondary)",
            }}
          >
            1. YOUR FACE
          </div>
          <div
            {...getSourceProps()}
            style={{
              border:
                "2px dashed " +
                (sourceActive ? "var(--cyan)" : "var(--bg-border)"),
              borderRadius: "var(--radius-md)",
              background: sourceActive
                ? "var(--cyan-glow)"
                : "var(--bg-elevated)",
              aspectRatio: "1/1",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              overflow: "hidden",
              position: "relative",
            }}
          >
            <input {...getSourceInput()} />
            {sourceFile ? (
              <img
                src={sourceFile.preview}
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
                alt="Source"
              />
            ) : (
              <div style={{ textAlign: "center", padding: "1rem" }}>
                <div
                  style={{
                    fontSize: "2rem",
                    marginBottom: "0.5rem",
                    opacity: 0.4,
                  }}
                >
                  👤
                </div>
                <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  Click or Drag Face Image
                </div>
              </div>
            )}
          </div>
        </Card>
        <Card>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "1rem",
            }}
          >
            <div
              style={{
                fontWeight: 700,
                fontSize: "0.9rem",
                color: "var(--text-secondary)",
              }}
            >
              2. CHOOSE TEMPLATE
            </div>
            <div {...getCustomProps()}>
              <input {...getCustomInput()} />
              <Button size="sm" variant="subtle">
                Upload Custom
              </Button>
            </div>
          </div>
          {templateFile && (
            <div
              style={{
                marginBottom: "1rem",
                padding: "0.5rem",
                background: "var(--bg-elevated)",
                borderRadius: "var(--radius-sm)",
                display: "flex",
                alignItems: "center",
                gap: "0.75rem",
                border: "1px solid var(--cyan-glow)",
              }}
            >
              <Thumb src={templateFile.preview} size={40} />
              <div
                style={{
                  fontSize: "0.75rem",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                <div
                  style={{ color: "var(--text-muted)", fontSize: "0.65rem" }}
                >
                  Selected:
                </div>
                <div style={{ color: "var(--cyan)", fontWeight: 700 }}>
                  {templateFile.filename}
                </div>
              </div>
            </div>
          )}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(60px, 1fr))",
              gap: "0.5rem",
              maxHeight: 300,
              overflowY: "auto",
              paddingRight: "0.5rem",
            }}
          >
            {templates.map((t) => (
              <div
                key={t}
                onClick={() => selectGridTemplate(t)}
                style={{
                  aspectRatio: "1/1",
                  cursor: "pointer",
                  borderRadius: "var(--radius-sm)",
                  border:
                    "2px solid " +
                    (templateFile && templateFile.filename === t
                      ? "var(--cyan)"
                      : "transparent"),
                  overflow: "hidden",
                  transition: "var(--transition)",
                }}
              >
                <img
                  src={API_BASE + "/templates/" + t}
                  alt={t}
                  style={{ width: "100%", height: "100%", objectFit: "cover" }}
                />
              </div>
            ))}
          </div>
        </Card>
        <Card>
          <div
            style={{
              fontWeight: 700,
              marginBottom: "1rem",
              fontSize: "0.9rem",
              color: "var(--text-secondary)",
            }}
          >
            3. RESULT
          </div>
          <div
            style={{
              background: "var(--bg-elevated)",
              borderRadius: "var(--radius-md)",
              aspectRatio: "1/1",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              overflow: "hidden",
              position: "relative",
              border: "1px solid var(--bg-border)",
            }}
          >
            {resultImage ? (
              <img
                src={resultImage}
                style={{ width: "100%", height: "100%", objectFit: "contain" }}
                alt="Result"
              />
            ) : isProcessing ? (
              <div style={{ textAlign: "center" }}>
                <Spinner size={40} />
                <div
                  style={{
                    marginTop: "1rem",
                    fontSize: "0.8rem",
                    color: "var(--cyan)",
                  }}
                >
                  Processing...
                </div>
                <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                  This takes ~10 seconds
                </div>
              </div>
            ) : (
              <div style={{ textAlign: "center", opacity: 0.3 }}>
                <div style={{ fontSize: "2rem" }}>✨</div>
                <div style={{ fontSize: "0.8rem" }}>
                  Result will appear here
                </div>
              </div>
            )}
          </div>
          {resultImage && (
            <div style={{ marginTop: "1rem" }}>
              <Button
                variant="primary"
                style={{ width: "100%" }}
                onClick={() => {
                  const link = document.createElement("a");
                  link.href = resultImage;
                  link.download = "faceswap_result.png";
                  link.click();
                }}
              >
                Download Result
              </Button>
            </div>
          )}
        </Card>
      </div>
      <Card
        style={{
          marginTop: "1.5rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "1.5rem" }}>
          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              cursor: "pointer",
              fontSize: "0.85rem",
            }}
          >
            <input
              type="checkbox"
              checked={enhance}
              onChange={(e) => setEnhance(e.target.checked)}
              style={{ accentColor: "var(--cyan)" }}
            />
            Enhance Quality (slower)
          </label>
          {error && (
            <div
              style={{
                color: "var(--red)",
                fontSize: "0.85rem",
                fontWeight: 700,
              }}
            >
              {"⚠️ " + error}
            </div>
          )}
          {warnings.length > 0 && (
            <div style={{ display: "flex", gap: "0.5rem" }}>
              {warnings.map((w, i) => (
                <Badge key={i} color="amber">
                  {w}
                </Badge>
              ))}
            </div>
          )}
        </div>
        <Button
          variant="primary"
          size="lg"
          disabled={!sourceFile || !templateFile || isProcessing}
          onClick={handleSwap}
        >
          {isProcessing ? "Processing..." : "SWAP FACES"}
        </Button>
      </Card>
    </div>
  );
}
