import { EmployeeAssistantClient } from "./employee-assistant-client";

export const metadata = {
  title: "Trợ lý AI | Vroom HR",
  description: "AI Assistant for employees — view your data and draft requests",
};

export default function AssistantPage() {
      return (
        <div className="animate-fade-in">
          <div className="mb-6 fade-in-section">
            <h1 className="text-2xl font-bold tracking-tight">Trợ lý AI</h1>
            <p className="text-muted-foreground">
              Hỏi về thông tin cá nhân, chấm công, yêu cầu nghỉ phép / tăng ca
            </p>
          </div>
          <div className="fade-in-section">
            <EmployeeAssistantClient />
          </div>
        </div>
  );
}
