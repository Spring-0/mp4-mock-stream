import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Upload } from 'lucide-react';

const VideoUpload = () => {
  const [uploading, setUploading] = useState(false);
  const [streamUrl, setStreamUrl] = useState("");
  const [error, setError] = useState("");
  const [expiryTime, setExpiryTime] = useState("");

  const handleUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Reset states
    setError("");
    setStreamUrl("");
    setUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("https://mp4-mock-stream.onrender.com/upload", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Upload failed");
      }

      setStreamUrl(data.stream_url);
      setExpiryTime(new Date(data.expires_at).toLocaleString());
    } catch (err) {
      setError(err.message || "Failed to upload video");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Video Upload To Generate HLS Stream</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <label 
              className={`
                flex flex-col items-center justify-center w-full h-32
                border-2 border-dashed rounded-lg
                cursor-pointer
                hover:bg-gray-50
                ${uploading ? "bg-gray-100 cursor-not-allowed" : "bg-white"}
              `}
            >
              <div className="flex flex-col items-center justify-center pt-5 pb-6">
                <Upload className="w-8 h-8 mb-2 text-gray-500" />
                <p className="text-sm text-gray-500">
                  {uploading ? "Uploading..." : "Click to upload video"}
                </p>
              </div>
              <input
                type="file"
                className="hidden"
                accept="video/mp4"
                onChange={handleUpload}
                disabled={uploading}
              />
            </label>

            {error && (
              <div className="p-3 text-sm text-red-500 bg-red-50 rounded">
                {error}
              </div>
            )}

            {streamUrl && (
              <div className="space-y-2">
                <div className="p-3 text-sm bg-green-50 text-green-700 rounded">
                  Upload successful!
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-medium">Stream URL:</p>
                  <p className="text-sm break-all bg-gray-50 p-2 rounded">
                    {streamUrl}
                  </p>
                  <p className="text-xs text-gray-500">
                    Expires at: {expiryTime}
                  </p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default VideoUpload;