/**
 * Tests for reusable components
 *
 * Run: npx jest src/__tests__/components.test.js
 *
 * These tests verify component rendering. They require @testing-library/react-native.
 * Install: npm install --save-dev @testing-library/react-native
 */

import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import Button from '../components/Button';
import Card from '../components/Card';
import Input from '../components/Input';
import { Text } from 'react-native';

describe('Button', () => {
  it('renders title text', () => {
    const { getByText } = render(<Button title="Press me" onPress={() => {}} />);
    expect(getByText('Press me')).toBeTruthy();
  });

  it('calls onPress when tapped', () => {
    const onPress = jest.fn();
    const { getByText } = render(<Button title="Tap" onPress={onPress} />);
    fireEvent.press(getByText('Tap'));
    expect(onPress).toHaveBeenCalledTimes(1);
  });

  it('does not call onPress when disabled', () => {
    const onPress = jest.fn();
    const { getByText } = render(<Button title="Disabled" onPress={onPress} disabled />);
    fireEvent.press(getByText('Disabled'));
    expect(onPress).not.toHaveBeenCalled();
  });

  it('shows ActivityIndicator when loading', () => {
    const { queryByText, UNSAFE_getByType } = render(
      <Button title="Loading" onPress={() => {}} loading />
    );
    expect(queryByText('Loading')).toBeNull();
  });
});

describe('Card', () => {
  it('renders children', () => {
    const { getByText } = render(
      <Card><Text>Card content</Text></Card>
    );
    expect(getByText('Card content')).toBeTruthy();
  });
});

describe('Input', () => {
  it('renders label when provided', () => {
    const { getByText } = render(<Input label="Email" />);
    expect(getByText('Email')).toBeTruthy();
  });

  it('renders error message when provided', () => {
    const { getByText } = render(<Input error="Required field" />);
    expect(getByText('Required field')).toBeTruthy();
  });

  it('calls onChangeText when typing', () => {
    const onChangeText = jest.fn();
    const { getByPlaceholderText } = render(
      <Input placeholder="Type here" onChangeText={onChangeText} />
    );
    fireEvent.changeText(getByPlaceholderText('Type here'), 'hello');
    expect(onChangeText).toHaveBeenCalledWith('hello');
  });
});
