"use client";

import * as React from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";

import { cn } from "@/lib/utils";

type DialogContextValue = {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
};

const DialogContext = React.createContext<DialogContextValue | null>(null);

function useDialogContext() {
  const context = React.useContext(DialogContext);

  if (!context) {
    throw new Error("Dialog components must be used inside Dialog.");
  }

  return context;
}

export function Dialog({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = React.useState(false);

  return (
    <DialogContext.Provider value={{ open, setOpen }}>
      {children}
    </DialogContext.Provider>
  );
}

export function DialogTrigger({
  asChild,
  children,
}: {
  asChild?: boolean;
  children: React.ReactNode;
}) {
  const { setOpen } = useDialogContext();

  if (asChild && React.isValidElement(children)) {
    const child = children as React.ReactElement<{
      onClick?: React.MouseEventHandler;
    }>;

    return React.cloneElement(child, {
      onClick: (event: React.MouseEvent) => {
        child.props.onClick?.(event);
        setOpen(true);
      },
    });
  }

  return <button onClick={() => setOpen(true)}>{children}</button>;
}

export interface DialogContentProps
  extends React.HTMLAttributes<HTMLDivElement> {
  from?: "top" | "bottom" | "left" | "right" | "center";
  showCloseButton?: boolean;
}

export function DialogContent({
  children,
  className,
  from = "center",
  showCloseButton = true,
  ...props
}: DialogContentProps) {
  const { open, setOpen } = useDialogContext();

  React.useEffect(() => {
    if (!open) {
      return;
    }

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, setOpen]);

  React.useEffect(() => {
    if (!open) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  if (typeof document === "undefined" || !open) {
    return null;
  }

  return createPortal(
    <div className="fixed inset-0 z-[100] flex items-center justify-center px-4 py-8">
      <button
        type="button"
        aria-label="Close dialog"
        className="absolute inset-0 bg-black/40"
        onClick={() => setOpen(false)}
      />
      <div
        className={cn(
          "relative w-full rounded-xl border border-shell-border bg-background p-5 shadow-[0_18px_40px_rgba(15,23,42,0.16)]",
          fromClassName[from],
          className,
        )}
        {...props}
      >
        {showCloseButton ? (
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="absolute right-3 top-3 inline-flex h-8 w-8 items-center justify-center rounded-md text-foreground/60 transition hover:bg-panel hover:text-foreground"
          >
            <X className="h-4 w-4" />
            <span className="sr-only">Close</span>
          </button>
        ) : null}
        {children}
      </div>
    </div>,
    document.body,
  );
}

export function DialogHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("grid gap-1.5", className)} {...props} />;
}

export function DialogTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h2
      className={cn("text-lg font-semibold text-foreground", className)}
      {...props}
    />
  );
}

export function DialogDescription({
  className,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cn("text-sm leading-7 text-foreground/70", className)} {...props} />
  );
}

export function DialogFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("mt-6 flex flex-wrap items-center justify-end gap-2", className)}
      {...props}
    />
  );
}

export function DialogClose({
  asChild,
  children,
}: {
  asChild?: boolean;
  children: React.ReactNode;
}) {
  const { setOpen } = useDialogContext();

  if (asChild && React.isValidElement(children)) {
    const child = children as React.ReactElement<{
      onClick?: React.MouseEventHandler;
    }>;

    return React.cloneElement(child, {
      onClick: (event: React.MouseEvent) => {
        child.props.onClick?.(event);
        setOpen(false);
      },
    });
  }

  return <button onClick={() => setOpen(false)}>{children}</button>;
}

const fromClassName: Record<NonNullable<DialogContentProps["from"]>, string> = {
  center: "max-w-lg",
  top: "max-w-lg self-start mt-10",
  bottom: "max-w-lg self-end mb-10",
  left: "max-w-lg mr-auto",
  right: "max-w-lg ml-auto",
};
