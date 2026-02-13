#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { BodoFrontendStack } from '../lib/frontend-stack';

const app = new cdk.App();

new BodoFrontendStack(app, 'BodoFrontendStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'ap-northeast-2', // 서울 리전 기본값
  },
  description: 'Bodo Frontend Infrastructure Stack',
});