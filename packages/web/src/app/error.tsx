'use client';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="container mx-auto px-4 py-8 text-center">
      <h2 className="text-2xl font-bold text-red-500 mb-4">出错了</h2>
      <p className="text-gray-400 mb-4">{error.message}</p>
      <button
        onClick={() => reset()}
        className="btn btn-primary"
      >
        重试
      </button>
    </div>
  );
}
