import { unstable_cache } from "next/cache";
import { CACHE_STALE_TIME } from "@/lib/constants";
import { QUERY_KEYS } from "@/lib/query-keys";
import { type MyClass } from "@my-project/types";
import { HomeService } from "@/lib/services";

const homeService = new HomeService();

export async function fetchMessagesCached(userId: string): Promise<MyClass[]> {
  return unstable_cache(
    async () => {
      return await homeService.fetchMessages();
    },
    [...QUERY_KEYS.messages(userId)],
    {
      tags: [...QUERY_KEYS.messages(userId)],
      revalidate: CACHE_STALE_TIME,
    },
  )();
}
