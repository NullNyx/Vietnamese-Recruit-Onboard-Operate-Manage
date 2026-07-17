import { Bot } from 'lucide-react';
import { ChatInterface } from '@/components/assistant/chat-interface';

export const metadata = {
  title: 'Trợ lý AI | Vroom HR',
  description: 'AI Assistant cho quản trị viên HR',
};

export default function AssistantPage() {
  return (
    <div className="animate-fade-in">
      <div className="mb-6 fade-in-section flex items-start gap-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10">
          <Bot className="h-5 w-5 text-primary" />
        </div>
        <div>
              <h1 className="font-heading text-2xl font-bold tracking-tight">
                Trợ lý AI
              </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Hỏi đáp về dữ liệu tuyển dụng, onboarding, và soạn email
          </p>
        </div>
      </div>
      <div className="fade-in-section">
        <ChatInterface />
      </div>
    </div>
  );
}
