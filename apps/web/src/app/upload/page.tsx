import { UploadForm } from "@/components/upload/upload-form";

export default function UploadPage() {
  return (
    <div className="space-y-8">
      <div className="animate-fade-in border-b border-border pb-5">
        <h1 className="page-title">Upload</h1>
        <p className="text-sm text-muted-foreground mt-1.5">
          Generic small-asset upload (up to 100 MB per file), proxied through
          the API. To add a video to the archive — including multi-GB files —
          use <span className="font-medium">Library → Add video</span>, which
          streams directly to B2 with presigned multipart.
        </p>
      </div>
      <div className="animate-fade-in-up stagger-2">
        <UploadForm />
      </div>
    </div>
  );
}
