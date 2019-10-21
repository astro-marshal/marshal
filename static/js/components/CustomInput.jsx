import React from 'react';
import PropTypes from 'prop-types';
import styles from './Input.css';


const CustomInput = ({ type, name, value, onChange, placeholder, size, disabled, label }) => (
  <div className={styles.inputWrapper}>
    <div className={styles.labelWrapper}>
      <label htmlFor={name} className={styles.label}>
        {label}
      </label>
    </div>
    <input
      className={styles.input}
      type={type}
      name={name}
      value={value}
      onChange={onChange}
      size={size}
      placeholder={placeholder}
      disabled={disabled}
    />
  </div>
);

CustomInput.propTypes = {
  type: PropTypes.oneOf(['number', 'text']).isRequired,
  name: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([
    PropTypes.number,
    PropTypes.string
  ]).isRequired,
  onChange: PropTypes.func.isRequired,
  size: PropTypes.string,
  placeholder: PropTypes.string,
  disabled: PropTypes.bool,
  label: PropTypes.string,
};

CustomInput.defaultProps = {
  size: "6",
  placeholder: null,
  disabled: false,
  label: null,
};


export default CustomInput;
