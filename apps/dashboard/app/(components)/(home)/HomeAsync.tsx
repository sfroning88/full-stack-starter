import { use } from "react";
import type { VolcanoDashboard } from "@fiery/types";
import { HomePanel } from "./HomePanel";

type HomeAsyncProps = {
  initialDataPromise: Promise<VolcanoDashboard[]>;
};

export function HomeAsync({ initialDataPromise }: HomeAsyncProps) {
  const initialData = use(initialDataPromise);
  return <HomePanel initialData={initialData} />;
}
