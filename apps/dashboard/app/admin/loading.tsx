import { AdminSkeleton } from "@/app/(components)/(admin)/AdminSkeleton";

export default function AdminLoading() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1 animate-pulse">
        <div className="h-8 w-24 rounded bg-zinc-200 dark:bg-white/10" />
        <div className="h-4 w-64 rounded bg-zinc-100 dark:bg-white/5 mt-1" />
      </div>
      <AdminSkeleton />
    </div>
  );
}
