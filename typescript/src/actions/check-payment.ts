import type {
  Action,
  ActionResult,
  HandlerCallback,
  HandlerOptions,
  IAgentRuntime,
  JsonValue,
  Memory,
  State,
} from "@elizaos/core";

import type { MysticismService } from "../services/mysticism-service";

export const checkPaymentAction: Action = {
  name: "CHECK_PAYMENT",
  similes: ["VERIFY_PAYMENT", "PAYMENT_STATUS"],
  description: "Check if payment has been received for the current reading session.",

  validate: async (
    runtime: IAgentRuntime,
    message: Memory,
    _state: State | undefined
  ): Promise<boolean> => {
    const service = runtime.getService<MysticismService>("MYSTICISM");
    if (!service) return false;
    const session = service.getSession(message.entityId, message.roomId);
    return session !== null && session.paymentStatus !== "none";
  },

  handler: async (
    runtime: IAgentRuntime,
    message: Memory,
    _state?: State,
    _options?: HandlerOptions | Record<string, JsonValue | undefined>,
    _callback?: HandlerCallback
  ): Promise<ActionResult | undefined> => {
    const service = runtime.getService<MysticismService>("MYSTICISM");
    if (!service) {
      return { success: false, text: "Mysticism service not available." };
    }

    const session = service.getSession(message.entityId, message.roomId);
    if (!session) {
      return { success: false, text: "No active session." };
    }

    return {
      success: true,
      text: `Payment status: ${session.paymentStatus}`,
      data: {
        paymentStatus: session.paymentStatus,
        amount: session.paymentAmount,
        txHash: session.paymentTxHash,
        readingType: session.type,
      },
    };
  },

  examples: [
    [
      {
        name: "{{agentName}}",
        content: {
          text: "Let me check if your payment has come through...",
          actions: ["CHECK_PAYMENT"],
        },
      },
    ],
  ],
};
