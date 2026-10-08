import { use } from "react";
import type { MyClass } from "@my-project/types";
import { HomePanel } from "./HomePanel";

type HomeAsyncProps = {
  initialMessagesPromise: Promise<MyClass[]>;
  canSendMessage: boolean;
};

export function HomeAsync({
  initialMessagesPromise,
  canSendMessage,
}: HomeAsyncProps) {
  const initialMessages = use(initialMessagesPromise);
  return (
    <HomePanel
      initialMessages={initialMessages}
      canSendMessage={canSendMessage}
    />
  );
}
