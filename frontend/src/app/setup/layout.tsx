/** Setup wizard layout — centered card on beige bg */

export default function SetupLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#FAF9F6]">
      {children}
    </div>
  );
}
