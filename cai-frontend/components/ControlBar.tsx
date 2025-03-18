

export function ControlBar({
  onConnectButtonClicked,
  agentState,
}: {
  onConnectButtonClicked: () => void;
  agentState: string;
}) {
  return (
    <div className="flex justify-center gap-4 mt-4">
      <button onClick={onConnectButtonClicked} className="bg-green-500 hover:bg-green-600">
        {agentState === "connected" ? "Connected" : "Connect"}
      </button>
    </div>
  );
}
