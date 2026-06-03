"use client";

import { useRef } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormMessage,
} from "@/components/ui/form";

import {
  domainAddSchema,
  type DomainAddFormData,
} from "@/lib/api/admin-schemas";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface DomainAddFormProps {
  onAdd: (domain: string) => Promise<void>;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function DomainAddForm({ onAdd }: DomainAddFormProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const form = useForm<DomainAddFormData>({
    resolver: zodResolver(domainAddSchema),
    defaultValues: { domain: "" },
  });

  const handleSubmit = async (data: DomainAddFormData) => {
    await onAdd(data.domain);
    form.reset();
    inputRef.current?.focus();
  };

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(handleSubmit)}
        className="flex items-start gap-3"
      >
        <FormField
          control={form.control}
          name="domain"
          render={({ field }) => (
            <FormItem className="flex-1">
              <FormControl>
                <Input
                  placeholder="company.vn"
                  {...field}
                  ref={(e) => {
                    field.ref(e);
                    (inputRef as React.MutableRefObject<HTMLInputElement | null>).current = e;
                  }}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button
          type="submit"
          size="default"
          disabled={form.formState.isSubmitting}
        >
          {form.formState.isSubmitting ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <Plus className="mr-2 h-4 w-4" aria-hidden="true" />
          )}
          Thêm domain
        </Button>
      </form>
    </Form>
  );
}
