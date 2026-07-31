import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { useCategories, useCreateCategory } from "../hooks/useExpenses";
import { categorySchema, type CategoryFormValues } from "../schemas/expenseSchemas";

export function CategoryManager() {
  const [open, setOpen] = useState(false);
  const { data: categories, isLoading } = useCategories();
  const createCategory = useCreateCategory();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CategoryFormValues>({ resolver: zodResolver(categorySchema) });

  const onSubmit = (values: CategoryFormValues) =>
    createCategory.mutate(values, {
      onSuccess: () => {
        reset();
        setOpen(false);
      },
    });

  return (
    <div className="mx-auto max-w-2xl space-y-6 px-4 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Expense categories</h1>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>New category</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>New category</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="name">Name</Label>
                <Input id="name" {...register("name")} />
                {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="color">Color</Label>
                <Input id="color" type="color" {...register("color")} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="description">Description</Label>
                <Input id="description" {...register("description")} />
              </div>
              {createCategory.isError && (
                <p className="text-sm text-destructive">
                  A category with this name already exists.
                </p>
              )}
              <Button type="submit" className="w-full" disabled={createCategory.isPending}>
                {createCategory.isPending ? "Saving…" : "Create category"}
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {(categories ?? []).map((c) => (
            <div key={c.id} className="flex items-center gap-2 rounded-lg border border-border p-3">
              <span className="h-3 w-3 rounded-full" style={{ backgroundColor: c.color }} />
              <span className="text-sm">{c.name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
