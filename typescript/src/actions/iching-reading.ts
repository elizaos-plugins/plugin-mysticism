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
import { logger } from "@elizaos/core";

import type { MysticismService } from "../services/mysticism-service";

const ICHING_KEYWORDS: readonly string[] = [
  "i ching",
  "i-ching",
  "iching",
  "hexagram",
  "book of changes",
  "oracle",
  "consult the i ching",
  "cast hexagram",
  "throw coins",
  "yarrow stalks",
  "cast the coins",
  "divination",
  "changing lines",
];

function extractQuestion(text: string): string {
  const stripPatterns = [
    /(?:can you |could you |please |would you )?(?:consult |cast |throw |do )(?:the )?(?:i[- ]?ching|hexagram|oracle|coins|yarrow stalks?)?\s*(?:about|regarding|for|on)?\s*/i,
    /(?:i(?:'d| would) (?:like|love) (?:to )?)?(?:consult |cast |ask )(?:the )?(?:i[- ]?ching|oracle|hexagram)\s*(?:about|regarding|for|on)?\s*/i,
    /(?:what does the )?(?:i[- ]?ching|oracle|book of changes)\s*(?:say|think|reveal|show)?\s*(?:about|regarding|for|on)?\s*/i,
  ];

  let cleaned = text;
  for (const pattern of stripPatterns) {
    cleaned = cleaned.replace(pattern, "").trim();
  }

  if (cleaned.length < 5) {
    return "general guidance on the path forward";
  }

  return cleaned;
}

export const ichingReadingAction: Action = {
  name: "ICHING_READING",
  similes: ["CAST_HEXAGRAM", "CONSULT_ICHING", "THROW_COINS", "ORACLE_READING"],
  description:
    "Perform an I Ching divination reading by casting a hexagram and interpreting changing lines.",

  validate: async (
    runtime: IAgentRuntime,
    message: Memory,
    _state: State | undefined
  ): Promise<boolean> => {
    const text = (message.content.text ?? "").toLowerCase();

    const hasIChingIntent = ICHING_KEYWORDS.some((kw) => text.includes(kw));
    if (!hasIChingIntent) return false;

    const service = runtime.getService<MysticismService>("MYSTICISM");
    if (!service) {
      logger.warn("ICHING_READING validation failed: MysticismService not found");
      return false;
    }

    // Don't start a new reading if one is already active
    const entityId = message.entityId;
    const existingSession = service.getSession(entityId, message.roomId);
    if (existingSession) {
      logger.debug(
        { entityId, roomId: message.roomId, type: existingSession.type },
        "ICHING_READING skipped: active session exists"
      );
      return false;
    }

    return true;
  },

  handler: async (
    runtime: IAgentRuntime,
    message: Memory,
    _state?: State,
    _options?: HandlerOptions | Record<string, JsonValue | undefined>,
    callback?: HandlerCallback
  ): Promise<ActionResult | undefined> => {
    const service = runtime.getService<MysticismService>("MYSTICISM");
    if (!service) {
      logger.error("ICHING_READING handler: MysticismService not available");
      return { success: false, text: "The mysticism service is not available." };
    }

    const entityId = message.entityId;
    const text = message.content.text ?? "";

    const crisis = service.detectCrisis(text);
    if (crisis.detected && crisis.severity === "high") {
      if (callback) {
        await callback({
          text:
            "I sense you're carrying something very heavy right now. " +
            "Before we consult the oracle, I want you to know that there " +
            "are people who care and can help.\n\n" +
            crisis.recommendedAction,
        });
      }
      return {
        success: true,
        text: "Crisis detected — provided support resources instead of reading.",
      };
    }

    const question = extractQuestion(text);

    try {
      const session = service.startIChingReading(entityId, message.roomId, question);

      const castingSummary = service.getIChingCastingSummary(entityId, message.roomId);

      logger.info(
        {
          entityId,
          roomId: message.roomId,
          hexagram: session.iching?.hexagram.number,
          changingLines: session.iching?.castResult.changingLines.length,
          question,
        },
        "I Ching reading initiated"
      );

      return {
        success: true,
        text: `Cast hexagram ${session.iching?.hexagram.number}: ${session.iching?.hexagram.englishName}`,
        data: {
          sessionId: session.id,
          hexagramNumber: session.iching?.hexagram.number,
          hexagramName: session.iching?.hexagram.englishName,
          changingLineCount: session.iching?.castResult.changingLines.length,
          castingSummary,
          question,
        },
      };
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Unknown error casting hexagram";
      logger.error({ error: errorMsg }, "ICHING_READING handler failed");
      return { success: false, text: errorMsg };
    }
  },

  examples: [
    [
      {
        name: "{{user1}}",
        content: { text: "Can you consult the I Ching for me?" },
      },
      {
        name: "{{agentName}}",
        content: {
          text: "I'll cast the coins for you. Focus on your question as I throw them six times to build your hexagram...",
          actions: ["ICHING_READING"],
        },
      },
    ],
    [
      {
        name: "{{user1}}",
        content: { text: "I'd like to cast a hexagram about a decision I'm facing" },
      },
      {
        name: "{{agentName}}",
        content: {
          text: "The I Ching is wonderful for moments of decision. Let me cast the coins and see what wisdom emerges...",
          actions: ["ICHING_READING"],
        },
      },
    ],
    [
      {
        name: "{{user1}}",
        content: { text: "What does the Book of Changes say about my relationship?" },
      },
      {
        name: "{{agentName}}",
        content: {
          text: "Let me consult the ancient oracle about your relationship. The coins are cast...",
          actions: ["ICHING_READING"],
        },
      },
    ],
  ],
};
