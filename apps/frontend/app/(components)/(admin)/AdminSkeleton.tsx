export function AdminSkeleton() {
  return (
    <div className="space-y-4 animate-pulse font-data">
      <div className="h-24 rounded-md border border-myproject-gray-200 bg-white/50 dark:border-white/10 dark:bg-surface-dark" />
      <div className="space-y-2 rounded-md border border-myproject-gray-200 dark:border-white/10">
        {Array.from({ length: 3 }).map((_, index) => (
          <div
            key={index}
            className="h-16 border-b border-myproject-gray-100 px-4 py-3 last:border-0 dark:border-white/5"
          >
            <div className="h-3 w-48 rounded bg-myproject-gray-100 dark:bg-white/10" />
            <div className="mt-2 h-4 w-full max-w-sm rounded bg-myproject-gray-50 dark:bg-white/5" />
          </div>
        ))}
      </div>
    </div>
  );
}
