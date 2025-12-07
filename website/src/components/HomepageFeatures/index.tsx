import type { ReactNode } from "react";
import clsx from "clsx";
import Heading from "@theme/Heading";
import styles from "./styles.module.css";

type FeatureItem = {
  title: string;
  image: string;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: "Physical AI & Humanoid Robotics",
    image: "img/download.png",
    description: (
      <>
        We&apos;ve been working on physical AI and humanoid robotics for over a
        decade. Our expertise lies in creating lifelike robots that can interact
        seamlessly with humans.
      </>
    ),
  },
  {
    title: "The Robotic Nervous System",
    image: "img/nervious.png",
    description: (
      <>
        Our proprietary Robotic Nervous System (RNS) integrates advanced AI
        algorithms with cutting-edge hardware to deliver unparalleled
        performance in robotics applications.
      </>
    ),
  },
  {
    title: "Gazebo & Unity - The Digital Twin",
    image: "img/twin.png",
    description: (
      <>
        We utilize Gazebo and Unity to create digital twins of our robotic
        systems, allowing for precise simulations and testing in virtual
        environments before deployment in the real world.
      </>
    ),
  },
  {
    title: "NVIDIA Isaac - The AI-Robot Brain",
    image: "img/robot.png",
    description: (
      <>
        Leveraging NVIDIA Isaac, we develop intelligent robotic brains that
        enable autonomous decision-making and learning capabilities in our
        humanoid robots.
      </>
    ),
  },
  {
    title: "Vision-Language-Action (VLA) - The Complete System",
    image: "img/vla.png",
    description: (
      <>
        Our Vision-Language-Action (VLA) framework combines visual perception,
        natural language understanding, and action execution to create robots
        that can comprehend and respond to complex human instructions.
      </>
    ),
  },
];

function Feature({ title, image, description }: FeatureItem) {
  return (
    <div className={clsx("col col--4")}>
      <div className="text--center">
        <img src={image} className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
