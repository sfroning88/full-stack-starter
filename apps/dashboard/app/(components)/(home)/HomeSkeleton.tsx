export function HomeSkeleton() {
  return (
    <div className="space-y-4 font-data">
      <div className="h-8 w-56 rounded bg-white/10 animate-pulse" />
      <div className="flex h-[70vh] items-center justify-center border border-white/10 rounded-md bg-surface-dark">
        <div
          className="h-8 w-8 rounded-full border-2 border-white/15 border-t-fiery-crimson-400 animate-spin"
          aria-hidden
        />
      </div>
    </div>
  );
}
