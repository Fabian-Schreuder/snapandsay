"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useAgent } from "@/hooks/use-agent";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface TextEntryModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function TextEntryModal({ isOpen, onClose }: TextEntryModalProps) {
  const [text, setText] = useState("");
  const { submitText } = useAgent();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const t = useTranslations();
  const te = useTranslations("snap.textEntry");

  const handleSubmit = async () => {
    if (!text.trim()) return;

    try {
      setIsSubmitting(true);
      await submitText(text);
      setText("");
      onClose();
    } catch (error) {
      console.error("Failed to submit text:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      onClose();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{te("title")}</DialogTitle>
          <DialogDescription>{te("description")}</DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <Textarea
            placeholder={te("placeholder")}
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="min-h-[100px]"
          />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
            {t("common.cancel")}
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!text.trim() || isSubmitting}
          >
            {isSubmitting ? te("logging") : te("title")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
