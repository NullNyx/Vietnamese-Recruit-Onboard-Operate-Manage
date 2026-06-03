import { ChatInterface } from "@/components/assistant/chat-interface";

export const metadata = {
  title: "Trợ lý AI | Vroom HR",
  description: "AI Assistant for HR administrators",
};

export default function AssistantPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Trợ lý AI</h1>
        <p className="text-muted-foreground">
          Hỏi đáp về dữ liệu tuyển dụng, onboarding, và soạn email
        </p>
      </div>
      <ChatInterface />
    </div>
  );
}
