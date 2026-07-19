import { Loader2 } from "lucide-react";
import { useMemo, useState } from "react";
import { ForceGraph } from "@/components/ForceGraph";
import { Badge } from "@/components/ui/Badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { useConceptMap } from "@/hooks/queries";

const SUBJECT = "az-900";

function communityColorVar(community: number): string {
  return `var(--color-community-${(Math.abs(community) % 8) + 1})`;
}

export default function ConceptMap() {
  const { data, isLoading, isError } = useConceptMap(SUBJECT);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const selectedNode = useMemo(
    () => data?.nodes.find((n) => n.id === selectedId) ?? null,
    [data, selectedId],
  );
  const selectedCommunity = useMemo(() => {
    if (!data || !selectedNode) return null;
    return data.communities.find((c) => c.id === selectedNode.community) ?? null;
  }, [data, selectedNode]);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Concept map</h1>
        <p className="text-muted-foreground">
          Concepts and their relationships across the syllabus, grouped into communities.
          {data && (
            <Badge tone="neutral" className="ml-2 align-middle">
              backend: {data.backend}
            </Badge>
          )}
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_20rem]">
        <Card className="overflow-hidden">
          <CardContent className="p-0">
            <div className="aspect-[928/560] w-full bg-muted/20">
              {isLoading && (
                <div className="flex h-full items-center justify-center text-muted-foreground">
                  <Loader2 className="size-6 animate-spin" />
                </div>
              )}
              {isError && (
                <div className="flex h-full items-center justify-center text-danger">
                  Failed to load the concept map.
                </div>
              )}
              {data && (
                <ForceGraph
                  nodes={data.nodes}
                  edges={data.edges}
                  selectedId={selectedId}
                  onSelect={setSelectedId}
                />
              )}
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card className="lg:sticky lg:top-20">
            <CardHeader>
              <CardTitle>{selectedNode ? selectedNode.label : "Select a concept"}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {selectedCommunity ? (
                <>
                  <p className="font-medium">{selectedCommunity.title}</p>
                  <p className="text-muted-foreground">
                    {selectedCommunity.summary || "No summary available for this community."}
                  </p>
                </>
              ) : (
                <p className="text-muted-foreground">
                  Click a node to see the community it belongs to and how its concepts connect. Drag
                  nodes to explore.
                </p>
              )}
            </CardContent>
          </Card>

          {data && data.communities.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Communities</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm">
                  {data.communities.map((c) => (
                    <li key={c.id} className="flex items-center gap-2">
                      <span
                        className="inline-block size-3 shrink-0 rounded-full"
                        style={{ backgroundColor: communityColorVar(c.id) }}
                        aria-hidden
                      />
                      <span className="truncate">{c.title}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
