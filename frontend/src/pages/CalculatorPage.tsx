import { Layout } from '../components/layout/Layout';
import { CalculatorForm } from '../components/calculator/CalculatorForm';
import { RouteResults } from '../components/calculator/RouteResults';
import { RouteMap } from '../components/map/RouteMap';
import { useCalculatorStore } from '../stores/calculatorStore';

export function CalculatorPage() {
  const { routeResult } = useCalculatorStore();

  return (
    <Layout>
      <div className="flex flex-col lg:flex-row min-h-[calc(100vh-64px)]">
        {/* Left Side - Form and Results */}
        <div className="w-full lg:w-1/2 p-6 lg:p-10 overflow-y-auto bg-background">
          <div className="max-w-md mx-auto lg:mx-0">
            <div className="mb-8">
              <h1 className="text-3xl lg:text-4xl font-bold text-foreground tracking-tight">
                Carbon
                <br />
                Calculator
              </h1>
              <p className="text-muted-foreground mt-3 text-base">
                Calculate and compare carbon emissions for your cargo shipments
              </p>
            </div>

            <CalculatorForm />

            {routeResult && (
              <div className="mt-6">
                <RouteResults result={routeResult} />
              </div>
            )}
          </div>
        </div>

        {/* Right Side - Full Map */}
        <div className="w-full lg:w-1/2 h-[50vh] lg:h-auto lg:fixed lg:right-0 lg:top-16 lg:bottom-0">
          <RouteMap routeResult={routeResult} />
        </div>
      </div>
    </Layout>
  );
}
