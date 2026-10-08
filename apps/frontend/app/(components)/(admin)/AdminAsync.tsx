import { use } from "react";
import type { MyClass } from "@my-project/types";
import { AdminPanel } from "./AdminPanel";

type AdminAsyncProps = {
  initialMessagesPromise: Promise<MyClass[]>;
};

export function AdminAsync({ initialMessagesPromise }: AdminAsyncProps) {
  const initialMessages = use(initialMessagesPromise);
  return <AdminPanel initialMessages={initialMessages} />;
}
