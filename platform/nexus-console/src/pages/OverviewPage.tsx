import { NavigationHub } from '../components/panels/Navigation/NavigationHub';
import { HealthMonitor } from '../components/panels/Health/HealthMonitor';

export default function OverviewPage() {
  return (
    <>
      <HealthMonitor />
      <NavigationHub />
    </>
  );
}
