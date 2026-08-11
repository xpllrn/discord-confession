import raw from "./commands.json";

export type CommandRow = {
  name: string;
  description: string;
  category: string;
  permission?: string;
};

export const commands: CommandRow[] = raw as CommandRow[];

export const totalAll = commands.length;

export const categories = [...new Set(commands.map((c) => c.category))];
