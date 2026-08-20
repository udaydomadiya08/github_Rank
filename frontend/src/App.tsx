
import { Dashboard } from './pages/Dashboard';

function App() {
  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      {/* Background gradients for modern aesthetic */}
      <div className="absolute top-0 left-0 w-full h-96 bg-primary/10 blur-[120px] rounded-full -translate-y-1/2 pointer-events-none"></div>
      <div className="absolute top-1/4 right-0 w-96 h-96 bg-secondary/10 blur-[120px] rounded-full translate-x-1/2 pointer-events-none"></div>
      
      <main className="relative z-10">
        <Dashboard />
      </main>
    </div>
  );
}

export default App;
