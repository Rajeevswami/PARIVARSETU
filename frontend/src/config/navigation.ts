import type { LucideIcon } from "lucide-react";
import { Bell, FileText, LayoutDashboard, Landmark, Receipt, Settings, Users } from "lucide-react";
export type NavigationItem={label:string;to:string;icon:LucideIcon;roles?:string[]};
export const navigation:NavigationItem[]=[{label:"Dashboard",to:"/",icon:LayoutDashboard},{label:"Members",to:"/members",icon:Users},{label:"Expenses",to:"/expenses",icon:Receipt},{label:"Loans",to:"/loans",icon:Landmark},{label:"Documents",to:"/documents",icon:FileText},{label:"Notifications",to:"/notifications",icon:Bell},{label:"Audit logs",to:"/audit",icon:FileText,roles:["family_admin"]},{label:"Settings",to:"/settings",icon:Settings},{label:"Family",to:"/family",icon:Settings,roles:["family_admin"]}];
export function visibleNavigation(role?:string){return navigation.filter(item=>!item.roles||item.roles.includes(role??""));}

