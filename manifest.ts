import type { MetadataRoute } from "next";
export default function manifest(): MetadataRoute.Manifest {
  return { name:"LIFE — Personal Life OS", short_name:"LIFE", description:"Your personal command center.", start_url:"/life", display:"standalone", background_color:"#f6f7f9", theme_color:"#f6f7f9", icons:[] };
}
