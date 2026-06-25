import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <header className="border-b border-border/40 sticky top-0 bg-background/80 backdrop-blur-sm z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-heading text-xl font-semibold text-primary">
              Vroom HR
            </span>
          </div>
          <nav className="hidden md:flex items-center gap-6 text-sm text-muted-foreground">
            <Link href="#backbone" className="hover:text-foreground transition-colors">
              Quy trình
            </Link>
            <Link href="#features" className="hover:text-foreground transition-colors">
              Tính năng
            </Link>
            <Link href="#open-source" className="hover:text-foreground transition-colors">
              Open Source
            </Link>
            <Link href="/docs" className="hover:text-foreground transition-colors">
              Tài liệu
            </Link>
          </nav>
          <div className="flex items-center gap-3">
            <Link href="/docs">
              <Button variant="ghost" size="sm">
                Tài liệu
              </Button>
            </Link>
            <Link href="/login">
              <Button size="sm">Đăng nhập</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 sm:py-28 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-secondary text-sm text-muted-foreground mb-6">
            <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
            Open Source — Self-Hosted
          </div>
          <h1 className="font-heading text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-foreground mb-6">
            Nền tảng quản lý nhân sự
            <br />
            <span className="text-primary">cho doanh nghiệp Việt Nam</span>
          </h1>
          <p className="text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
            Vroom HR giúp bạn đi từ email tuyển dụng đến nhân viên active trong cùng một mạch liên tục — 
            có kiểm soát, có audit, và tự host trên hạ tầng của bạn.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link href="/login">
              <Button size="lg" className="px-8">
                Dùng thử
              </Button>
            </Link>
            <Link href="#open-source">
              <Button variant="outline" size="lg" className="px-8">
                Tự host
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Backbone Flow */}
      <section id="backbone" className="py-20 px-4 bg-secondary/30">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="font-heading text-2xl sm:text-3xl font-semibold mb-4">
              Backbone Flow
            </h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              Đây là luồng chính của Vroom HR — mọi tính năng đều phục vụ cho mạch recruit-to-onboard này.
            </p>
          </div>
          
          <div className="flex flex-wrap justify-center items-center gap-2 sm:gap-4">
            {[
              { label: "Email", icon: "📧" },
              { label: "AI classify", icon: "🤖" },
              { label: "CV parse", icon: "📄" },
              { label: "Candidate", icon: "👤" },
              { label: "HR review", icon: "👁️" },
              { label: "Interview", icon: "📅" },
              { label: "Accept", icon: "✅" },
              { label: "Onboarding", icon: "🚀" },
              { label: "Employee", icon: "👥" },
            ].map((step, i) => (
              <div key={step.label} className="flex items-center">
                <Card className="w-24 sm:w-32 text-center py-4">
                  <CardContent className="p-0">
                    <div className="text-2xl mb-1">{step.icon}</div>
                    <div className="text-xs font-medium">{step.label}</div>
                  </CardContent>
                </Card>
                {i < 8 && (
                  <svg className="w-4 h-4 sm:w-6 sm:h-6 text-muted-foreground mx-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                )}
              </div>
            ))}
          </div>

          <p className="text-center text-sm text-muted-foreground mt-8">
            Từ một email ứng viên đến nhân viên active — mỗi bước đều có audit, đều rõ ràng.
          </p>
        </div>
      </section>

      {/* Why Vroom HR */}
      <section className="py-20 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="font-heading text-2xl sm:text-3xl font-semibold mb-4">
              Tại sao Vroom HR
            </h2>
          </div>
          
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                title: "Tự host, tự kiểm soát",
                description: "Deploy trên hạ tầng của bạn. Dữ liệu nhạy cảm không rời khỏi server.",
              },
              {
                title: "Mã nguồn mở",
                description: "Kiểm tra code bất cứ lúc nào. Đảm bảo security và compliance.",
              },
              {
                title: "Phù hợp Việt Nam",
                description: "Thiết kế cho quy trình HR Việt Nam: BHXH, thuế, ngày nghỉ, phép...",
              },
              {
                title: "AI hỗ trợ, không tự quyết",
                description: "AI giúp tóm tắt CV, draft email — nhưng HR là người quyết định cuối.",
              },
              {
                title: "Audit đầy đủ",
                description: "Mọi hành động đều có log. Sẵn sàng đối soát khi cần.",
              },
              {
                title: "Docker deploy",
                description: "Khởi chạy trong vài phút với Docker Compose. Không phức tạp.",
              },
            ].map((item) => (
              <Card key={item.title}>
                <CardContent className="p-6">
                  <h3 className="font-semibold mb-2">{item.title}</h3>
                  <p className="text-sm text-muted-foreground">{item.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 px-4 bg-secondary/30">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="font-heading text-2xl sm:text-3xl font-semibold mb-4">
              Tính năng chính
            </h2>
          </div>
          
          <div className="space-y-4">
            {[
              {
                title: "Tuyển dụng & Pipeline",
                items: ["AI phân loại email ứng viên", "Parse CV tự động", "Pipeline quản lý ứng viên", "Lịch phỏng vấn gắn calendar"],
              },
              {
                title: "Onboarding",
                items: ["Checklist tự động khi accept ứng viên", "Theo dõi tiến độ từng bước", "Tạo Employee khi hoàn thành"],
              },
              {
                title: "Quản lý nhân sự",
                items: ["Hồ sơ nhân viên", "Phòng ban / chức vụ", "Yêu cầu nghỉ phép / overtime", "Xem payslip"],
              },
              {
                title: "AI Assistant",
                items: ["Đọc dữ liệu recruitment/onboarding", "Draft email phỏng vấn / chúc mừng", "HR xác nhận trước khi gửi"],
              },
            ].map((category) => (
              <Card key={category.title} className="max-w-2xl mx-auto">
                <CardContent className="p-6">
                  <h3 className="font-semibold mb-3 text-primary">{category.title}</h3>
                  <ul className="space-y-2">
                    {category.items.map((item) => (
                      <li key={item} className="flex items-center gap-2 text-sm">
                        <svg className="w-4 h-4 text-success shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        {item}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Open Source */}
      <section id="open-source" className="py-20 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="font-heading text-2xl sm:text-3xl font-semibold mb-6">
            Open Source, Self-Hosted
          </h2>
          <p className="text-muted-foreground mb-8">
            Vroom HR mở mã nguồn để bạn có thể tự kiểm tra, tự deploy, và tự vận hành. 
            Không phụ thuộc vendor, không bị lock-in.
          </p>
          
          <Card className="max-w-lg mx-auto mb-8">
            <CardContent className="p-6 text-left">
              <h3 className="font-semibold mb-4">Bắt đầu nhanh</h3>
              <pre className="bg-secondary p-4 rounded-md text-sm overflow-x-auto">
{`git clone https://github.com/your-org/vroom-hr
cd vroom-hr
docker compose up -d
# Truy cập http://localhost:3000`}
              </pre>
              <p className="text-xs text-muted-foreground mt-3">
                Yêu cầu: Docker, Docker Compose, PostgreSQL, Redis
              </p>
            </CardContent>
          </Card>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link href="https://github.com/your-org/vroom-hr" target="_blank">
              <Button variant="outline" size="lg">
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z" />
                </svg>
                GitHub
              </Button>
            </Link>
            <Link href="/docs">
              <Button variant="outline" size="lg">
                Tài liệu chi tiết
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-4 bg-primary text-primary-foreground">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="font-heading text-2xl sm:text-3xl font-semibold mb-4">
            Sẵn sàng dùng thử?
          </h2>
          <p className="opacity-90 mb-8">
            Deploy local hoặc dùng demo để trải nghiệm backbone flow đầu tiên.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link href="/login">
              <Button size="lg" variant="secondary">
                Dùng thử ngay
              </Button>
            </Link>
            <Link href="#open-source">
              <Button size="lg" variant="outline" className="border-primary-foreground text-primary-foreground hover:bg-primary-foreground hover:text-primary">
                Tự host
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 border-t">
        <div className="max-w-5xl mx-auto">
          <div className="grid sm:grid-cols-3 gap-8 mb-8">
            <div>
              <div className="font-heading text-lg font-semibold mb-4">Vroom HR</div>
              <p className="text-sm text-muted-foreground">
                Open-source HR platform cho doanh nghiệp Việt Nam.
              </p>
            </div>
            <div>
              <div className="font-semibold mb-4">Liên kết</div>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link href="#backbone" className="hover:text-foreground">Quy trình</Link></li>
                <li><Link href="#features" className="hover:text-foreground">Tính năng</Link></li>
                <li><Link href="#open-source" className="hover:text-foreground">Tự host</Link></li>
                <li><Link href="/docs" className="hover:text-foreground">Tài liệu</Link></li>
              </ul>
            </div>
            <div>
              <div className="font-semibold mb-4">Developers</div>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link href="https://github.com/your-org/vroom-hr" target="_blank" className="hover:text-foreground">GitHub</Link></li>
                <li><Link href="/docs" className="hover:text-foreground">API Docs</Link></li>
                <li><Link href="/docs" className="hover:text-foreground">Contributing</Link></li>
              </ul>
            </div>
          </div>
          <div className="pt-8 border-t text-center text-sm text-muted-foreground">
            © 2024 Vroom HR. MIT License.
          </div>
        </div>
      </footer>
    </div>
  );
}
