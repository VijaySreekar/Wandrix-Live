"use client";

import * as React from "react";
import { format } from "date-fns";
import type { Matcher } from "react-day-picker";
import { Calendar as CalendarIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

interface DatePickerProps {
  date?: Date;
  onDateChange?: (date: Date | undefined) => void;
  placeholder?: string;
  disabled?: boolean;
  disabledDays?: Matcher | Matcher[];
  className?: string;
}

export function DatePicker({
  date,
  onDateChange,
  placeholder = "Pick a date",
  disabled = false,
  disabledDays,
  className,
}: DatePickerProps) {
  const [open, setOpen] = React.useState(false);

  const handleSelect = (selectedDate: Date | undefined) => {
    onDateChange?.(selectedDate);
    setOpen(false);
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          disabled={disabled}
          className={cn(
            "h-11 w-full justify-start rounded-lg border border-[var(--planner-board-border)] bg-white/50 px-4 text-left font-normal text-[var(--planner-board-text)] transition-all duration-200 hover:bg-white hover:border-[var(--planner-board-cta)]",
            !date && "text-[var(--planner-board-muted-strong)]",
            className
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          {date ? format(date, "PPP") : <span>{placeholder}</span>}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <Calendar
          mode="single"
          selected={date}
          onSelect={handleSelect}
          captionLayout="dropdown"
          disabled={disabledDays ?? false}
          initialFocus
        />
      </PopoverContent>
    </Popover>
  );
}
