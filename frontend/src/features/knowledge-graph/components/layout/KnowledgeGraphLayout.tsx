interface Props {
  children: React.ReactNode;
}


export function KnowledgeGraphLayout({
  children,
}: Props) {

  return (
    <div className="
      flex
      h-full
      flex-col
      gap-4
    ">

      {children}

    </div>
  );
}