"use client";

import { useState, useEffect } from "react";
import { User, Phone, MapPin, Shield, Save, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";

interface ProfileData {
  full_name: string;
  email: string;
  phone: string | null;
  date_of_birth: string | null;
  gender: string | null;
  address: string | null;
  department_name: string | null;
  position_name: string | null;
  start_date: string | null;
  contract_type: string | null;
  id_number_masked: string | null;
  tax_code_masked: string | null;
  emergency_contact: string | null;
}

interface FormErrors {
  phone?: string;
  address?: string;
  emergency_contact?: string;
}

const PHONE_PATTERN = /^0\d{9}$/;

function validatePhone(value: string): string | undefined {
  if (!value) return undefined;
  if (!PHONE_PATTERN.test(value)) {
    return "Số điện thoại phải gồm 10 chữ số, bắt đầu bằng 0";
  }
  return undefined;
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "—";
  try {
    return new Date(dateStr).toLocaleDateString("vi-VN");
  } catch {
    return dateStr;
  }
}

function formatGender(gender: string | null): string {
  if (!gender) return "—";
  const map: Record<string, string> = {
    male: "Nam",
    female: "Nữ",
    other: "Khác",
  };
  return map[gender.toLowerCase()] || gender;
}

function formatContractType(type: string | null): string {
  if (!type) return "—";
  const map: Record<string, string> = {
    full_time: "Toàn thời gian",
    part_time: "Bán thời gian",
    contract: "Hợp đồng",
    intern: "Thực tập",
    probation: "Thử việc",
  };
  return map[type.toLowerCase()] || type;
}

export default function EmployeeProfilePage() {
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  // Editable form fields
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [emergencyContact, setEmergencyContact] = useState("");
  const [errors, setErrors] = useState<FormErrors>({});
  const [isDirty, setIsDirty] = useState(false);

  useEffect(() => {
    fetchProfile();
  }, []);

  async function fetchProfile() {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/ess/profile");
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(
          err?.detail?.message || `Lỗi tải hồ sơ (${res.status})`,
        );
      }
      const data: ProfileData = await res.json();
      setProfile(data);
      setPhone(data.phone || "");
      setAddress(data.address || "");
      setEmergencyContact(data.emergency_contact || "");
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Không thể tải hồ sơ cá nhân",
      );
    } finally {
      setLoading(false);
    }
  }

  function handlePhoneChange(value: string) {
    setPhone(value);
    setIsDirty(true);
    const error = validatePhone(value);
    setErrors((prev) => ({ ...prev, phone: error }));
  }

  function handleAddressChange(value: string) {
    setAddress(value);
    setIsDirty(true);
    if (value.length > 500) {
      setErrors((prev) => ({
        ...prev,
        address: "Địa chỉ không được vượt quá 500 ký tự",
      }));
    } else {
      setErrors((prev) => ({ ...prev, address: undefined }));
    }
  }

  function handleEmergencyContactChange(value: string) {
    setEmergencyContact(value);
    setIsDirty(true);
    if (value.length > 255) {
      setErrors((prev) => ({
        ...prev,
        emergency_contact: "Liên hệ khẩn cấp không được vượt quá 255 ký tự",
      }));
    } else {
      setErrors((prev) => ({ ...prev, emergency_contact: undefined }));
    }
  }

  function hasValidationErrors(): boolean {
    return Object.values(errors).some((e) => e !== undefined);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    // Validate before submit
    const phoneError = validatePhone(phone);
    if (phoneError) {
      setErrors((prev) => ({ ...prev, phone: phoneError }));
      return;
    }

    if (hasValidationErrors()) return;

    // Build payload with only changed fields
    const payload: Record<string, string | null> = {};
    if (phone !== (profile?.phone || "")) {
      payload.phone = phone || null;
    }
    if (address !== (profile?.address || "")) {
      payload.address = address || null;
    }
    if (emergencyContact !== (profile?.emergency_contact || "")) {
      payload.emergency_contact = emergencyContact || null;
    }

    if (Object.keys(payload).length === 0) {
      toast.info("Không có thay đổi nào để cập nhật");
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch("/api/v1/ess/profile", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(
          err?.detail?.message || `Cập nhật thất bại (${res.status})`,
        );
      }

      const updated: ProfileData = await res.json();
      setProfile(updated);
      setPhone(updated.phone || "");
      setAddress(updated.address || "");
      setEmergencyContact(updated.emergency_contact || "");
      setIsDirty(false);
      toast.success("Cập nhật hồ sơ thành công");
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Không thể cập nhật hồ sơ",
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold tracking-tight">Hồ sơ cá nhân</h1>
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-40" />
            </CardHeader>
            <CardContent className="space-y-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="space-y-2">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-5 w-48" />
                </div>
              ))}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-40" />
            </CardHeader>
            <CardContent className="space-y-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="space-y-2">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-5 w-48" />
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold tracking-tight">Hồ sơ cá nhân</h1>
        <Card>
          <CardContent className="p-6">
            <p className="text-muted-foreground">
              Không thể tải thông tin hồ sơ. Vui lòng thử lại sau.
            </p>
            <Button onClick={fetchProfile} className="mt-4">
              Thử lại
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">Hồ sơ cá nhân</h1>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Personal Information (Read-only) */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <User className="h-5 w-5" />
              Thông tin cá nhân
            </CardTitle>
            <CardDescription>
              Thông tin cơ bản — liên hệ HR để thay đổi
            </CardDescription>
          </CardHeader>
          <CardContent>
            <dl className="space-y-4">
              <div>
                <dt className="text-sm font-medium text-muted-foreground">
                  Họ và tên
                </dt>
                <dd className="text-sm mt-1">{profile.full_name}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">
                  Email
                </dt>
                <dd className="text-sm mt-1">{profile.email}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">
                  Ngày sinh
                </dt>
                <dd className="text-sm mt-1">
                  {formatDate(profile.date_of_birth)}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">
                  Giới tính
                </dt>
                <dd className="text-sm mt-1">{formatGender(profile.gender)}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">
                  Ngày bắt đầu
                </dt>
                <dd className="text-sm mt-1">
                  {formatDate(profile.start_date)}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">
                  Loại hợp đồng
                </dt>
                <dd className="text-sm mt-1">
                  {formatContractType(profile.contract_type)}
                </dd>
              </div>
            </dl>
          </CardContent>
        </Card>

        {/* Work Information (Read-only) */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Shield className="h-5 w-5" />
              Thông tin công việc
            </CardTitle>
            <CardDescription>
              Phòng ban, chức vụ và thông tin bảo mật
            </CardDescription>
          </CardHeader>
          <CardContent>
            <dl className="space-y-4">
              <div>
                <dt className="text-sm font-medium text-muted-foreground">
                  Phòng ban
                </dt>
                <dd className="text-sm mt-1">
                  {profile.department_name || "—"}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">
                  Chức vụ
                </dt>
                <dd className="text-sm mt-1">{profile.position_name || "—"}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">
                  Số CMND/CCCD
                </dt>
                <dd className="text-sm mt-1 font-mono">
                  {profile.id_number_masked || "—"}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">
                  Mã số thuế
                </dt>
                <dd className="text-sm mt-1 font-mono">
                  {profile.tax_code_masked || "—"}
                </dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      </div>

      {/* Editable Contact Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Phone className="h-5 w-5" />
            Thông tin liên hệ
          </CardTitle>
          <CardDescription>
            Bạn có thể cập nhật số điện thoại, địa chỉ và liên hệ khẩn cấp
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid gap-6 sm:grid-cols-2">
              {/* Phone */}
              <div className="space-y-2">
                <Label htmlFor="phone">
                  <Phone className="inline h-4 w-4 mr-1" />
                  Số điện thoại
                </Label>
                <Input
                  id="phone"
                  type="tel"
                  placeholder="0912345678"
                  value={phone}
                  onChange={(e) => handlePhoneChange(e.target.value)}
                  className={errors.phone ? "border-destructive" : ""}
                  aria-invalid={!!errors.phone}
                  aria-describedby={errors.phone ? "phone-error" : undefined}
                />
                {errors.phone && (
                  <p
                    id="phone-error"
                    className="text-sm text-destructive"
                    role="alert"
                  >
                    {errors.phone}
                  </p>
                )}
                <p className="text-xs text-muted-foreground">
                  Định dạng: 10 chữ số, bắt đầu bằng 0
                </p>
              </div>

              {/* Emergency Contact */}
              <div className="space-y-2">
                <Label htmlFor="emergency_contact">
                  <Shield className="inline h-4 w-4 mr-1" />
                  Liên hệ khẩn cấp
                </Label>
                <Input
                  id="emergency_contact"
                  type="text"
                  placeholder="Nguyễn Văn A - 0987654321"
                  value={emergencyContact}
                  onChange={(e) => handleEmergencyContactChange(e.target.value)}
                  className={
                    errors.emergency_contact ? "border-destructive" : ""
                  }
                  aria-invalid={!!errors.emergency_contact}
                  aria-describedby={
                    errors.emergency_contact
                      ? "emergency-contact-error"
                      : undefined
                  }
                  maxLength={255}
                />
                {errors.emergency_contact && (
                  <p
                    id="emergency-contact-error"
                    className="text-sm text-destructive"
                    role="alert"
                  >
                    {errors.emergency_contact}
                  </p>
                )}
              </div>
            </div>

            {/* Address (full width) */}
            <div className="space-y-2">
              <Label htmlFor="address">
                <MapPin className="inline h-4 w-4 mr-1" />
                Địa chỉ
              </Label>
              <Input
                id="address"
                type="text"
                placeholder="123 Đường ABC, Quận 1, TP.HCM"
                value={address}
                onChange={(e) => handleAddressChange(e.target.value)}
                className={errors.address ? "border-destructive" : ""}
                aria-invalid={!!errors.address}
                aria-describedby={errors.address ? "address-error" : undefined}
                maxLength={500}
              />
              {errors.address && (
                <p
                  id="address-error"
                  className="text-sm text-destructive"
                  role="alert"
                >
                  {errors.address}
                </p>
              )}
            </div>

            {/* Submit */}
            <div className="flex justify-end">
              <Button
                type="submit"
                disabled={submitting || !isDirty || hasValidationErrors()}
              >
                {submitting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Đang lưu...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Lưu thay đổi
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
